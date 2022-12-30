import sys
import io
import re
from math import ceil
from itertools import repeat
from functools import reduce
from shutil import which
from multiprocessing import Pool, cpu_count
import subprocess
import argparse
from tqdm import tqdm  # type: ignore
from ja_utils import get_re_word, get_re_split, get_re_word_relaxed, WAVE_DASH, \
    add_tagger_arg_group, tagger_from_args, NORMALIZE_FULLWIDTH_TILDE
from freq_utils import Storage, WordCounterGroup
from collections.abc import Sequence
from typing import Optional

DEFAULT_MIN_DOCS = 3
EXTRACTOR_VERSION = '3.0.6'  # Checked due to wikiextractor quirkiness

# The following markup is replaced with a space character.
# In several cases we also use the RE to delete the content between the tags, e.g.
# <chem>, <ref>.
# We do keep the content enclosed in <ins>, <del>, <poem>.
# A few more elements have a special handling outside RE_MARKUP (<score>, <ruby>).
RE_MARKUP = re.compile(
    r'<br( [^>]+)?>|'               # e.g. <br>, <br style="clear: both">
    r'<chem>[^<]*</chem>|'          # e.g. <chem>NH3 </chem>

    # e.g. <ref name="..."></ref>, <ref group="..." name="..."></ref>,
    # <ref name="Kath26/07/2011"> , "I Kathimeriní", .</ref>,
    # <ref name="2015/07/29 powersearch">Article "..." de Michael Lipka, paru ...</ref>,
    # sometimes opening/closing tags are on separate lines
    r'<ref\b[^>]*/ref>|'  # weird one line ref, e.g. <ref[oanda.com, March 9, 2022]/ref>
    r'<ref [^>]+>[^<]*</ref>|'          # one line
    r'<ref [^>]+>[^<]*$|^[^<]*</ref>|'  # two lines

    # Remnants of tables:
    r'^!.*=.*\||'                   # e.g. '! colspan="5" style=background:;|'
    # Catch anything that passes the sub-expression above:
    # - common unquoted attribute values:
    r'\bhidden=1\b|'
    # - quoted values, e.g. align="left",
    # - unquoted values upto "|" on the same line,
    #   e.g. 'frame-style = border: 1px solid rgb(200,200,200); |',
    # - unquoted values consisting of a single word, e.g. 'align=left'
    r'\b(rowspan|colspan|width|style|bgcolor|align|valign|frame-style|title-style|'
    r'content-style)\s*=\s*("[^"]*"|.*\||\w+|)|'

    # Code and formula placeholders:
    r'(codice|formula)_[0-9]+|'     # e.g. 'DNAformula_20', '様にcodice_1 の'

    # <ins>text</ins>, <del>text</del>,
    # randomly appearing <math>/</math> tags
    # <onlyinclude>/</onlyinclude>/<onlyinclude/> in pages only linking to another page:
    r'</?(ins|del|math|onlyinclude)>|<onlyinclude/>|'

    # e.g. <poem style="...">poem lines</poem> (or <q cite="夏目漱石『坊つちやん』">),
    # <section begin="Schaubild" /> or <section end="Schaubild" />
    r'<(poem|q|section)( [^>]+)?>|</(poem|q)>|'

    # Sometimes there are blocks of the following (desambiuation/redirection, etc.)
    r'<ns>.*?</ns>|'
    r'<parentid>.*?</parentid>|'
    r'<revision>|'
    r'<timestamp>.*?</timestamp>|'
    r'</?contributor>|'
    r'<username>.*?</username>|'
    r'<minor />|'
    r'<comment>.*?</comment>|'
    r'<model>.*?</model>|'
    r'<format>.*?</format>'

    # TODO: fix wikiextractor instead?
    # We are still not filtering these:
    # - very long <mapframe>...</mapframe> blocks
    # - untagged math formulas (containing \mathbf etc.)
    # - untagged musical scores (see maybe_score, 'Warning: Possible score without ')
    # - the following spurious tokens in English/Penn word list:
    #   - height=
    #   - name=
    #   - zoom=
    #   - longitude=
    #   - type=
    #   - text=
    #   - |birth_date
    #   - /includeonly
    #   - /div
    #   - /ref
    #   - //www.youtube.com/watch
    # ... all of which contribute to spurious tokens.
    #
    # Some other ideas for filtering:
    # - all URLs like in tubelex?
    # - math: \frac \mathbf \right \left \end \partial \sum_ \sqrt
    # - (?) option=com_content
    # - __NOEDITSECTION__, __notoc__
    # - Czech: _, __, ___, ______, __bezobsahu__, __obsah__, cs_cz,
    #   __staticképřesměrování__, jmeno_tabulky
    # -
    #
    # See https://github.com/attardi/wikiextractor/issues/300
    )

# Do not keep the content enclosed in <score> (musical scores spanning multiple lines).
# (We do keep what's before and after via a parenthesised RE group.)
RE_SCORE_OPEN   = re.compile(
    # non-greedy (.*?) before opening:
    r'(.*?)(<score( [^>]+)?>|(?P<maybe>'
    # If <score> is missing match any of the following as a "maybe opening" of a score
    r'\\override Score\.\b|'
    r'\\new Staff\b|'
    r'\\new PianoStaff\b|'
    r'\\relative c\b|'
    r'\\clef\b|'
    r'\\unfoldRepeats\b))'
    )
RE_SCORE_CLOSE  = re.compile(r'</score>(.*)')

# Within <ruby>:
# Keep untagged content or content tagged <rb> (the base text).
# Do not keep content in <rp> (ruby parents) or <rt> (ruby text, i.e. furigana)
RE_RUBY     = re.compile(r'<ruby( [^>]+)?>(?P<content>.*?)</ruby>')  # .*? non-greedy
RE_RUBY_DEL = re.compile(r'<rp>[^<]*</rp>|<rt( [^>]+)?>[^<]*</rt>|</?rb>')


# Optimizations:
sub_markup          = RE_MARKUP.sub
sub_ruby_del        = RE_RUBY_DEL.sub
sub_ruby            = RE_RUBY.sub
search_score_open   = RE_SCORE_OPEN.search
search_score_close  = RE_SCORE_CLOSE.search


def repl_ruby(m: re.Match) -> str:
    return sub_ruby_del('', m.group('content'))


def remove_markup(line: str) -> str:
    '''
    Uses sub_markup():

    >>> sub_markup('', '<chem>H2O </chem>')
    ''
    >>> sub_markup('', '<ref name=foobar></ref><ref group="bar" name="baz"></ref>')
    ''
    >>> sub_markup('', '1965<ref name="10.1016/0022-5193(65)90083-4">\\n')
    '1965'
    >>> sub_markup('', ' .</ref>, abcd<ref name="10.1073/pnas.74.11.5088">\\n')
    ', abcd'
    >>> sub_markup('', '.</ref>, efgh<ref name="10.1007/BF01796092">\\n')
    ', efgh'
    >>> sub_markup('', '.</ref><ref name="10.1038/441289a">in ref\\n')
    ''
    >>> sub_markup('', '! colspan="5" style=background:;|TEXT')
    'TEXT'
    >>> sub_markup('',
    ...     'style="background-color:#E9E9E9" align=right valign = "top" width=200 TEXT'
    ... ).strip()
    'TEXT'
    >>> sub_markup('', 'DNAformula_20様にcodice_1 の')
    'DNA様に の'
    >>> sub_markup('', '<onlyinclude></math></onlyinclude><ins>A</ins><del>B</del>')
    'AB'
    >>> sub_markup('', '<poem>p<poem style="text-align: right">q')
    'pq'
    >>> sub_markup('', 'p</poem>q</q>')
    'pq'

    Ruby and markup removal (replaced with a space):

    >>> remove_markup('<ruby>主信<rt>しゅしん</rt></ruby>')
    '主信'
    >>> remove_markup('<ruby><rb>世</rb><rp>（</rp><rt>よ</rt><rp>）</rp></ruby>を')
    '世を'
    >>> remove_markup(
    ...     '<ruby lang="en">nitrogen<rp>（</rp><rt lang="en-Kana">ナイトロジェン</rt>'
    ...     '<rp>）</rp></ruby>'
    ... )
    'nitrogen'
    >>> remove_markup('化学式 <chem>N_2</chem> で<ins>表され</ins>')
    '化学式   で 表され '
    '''
    return sub_ruby(repl_ruby, sub_markup(' ', line))


# The right single quote '’' (but not the left single quote) is allowed to occur
# inside ‘...’ as long as it is surrounded by \w from both sides (\b’\b in the RE).
# E.g. ‘It’s an apostrophe.’ => “It’s an apostrophe.”
#
# The following RE and replaceement function replaces:
# 1. legit single quotes by double quotes
# 2. primes that look like apostrophe
RSQUOTE2APOS: dict[int, int] = {ord('’'): ord('\'')}

RE_SMART_APOS     = re.compile(
    # Preserve -- has group(1)
    r'‘(([^‘’]*\b’\b)*[^‘’]*)’(?!s)|'   # paired single quotes, see `in_quotes` below
    # Replace by apostrophe:
    r'’|'                               # right single quote except pairs like above
    r'(?<=[A-Za-z]{2})′|'               # prime following at least two alphabet letters
    r'′(?=s)'                           # prime before 's'
    )
sub_smart_apos   = RE_SMART_APOS.sub  # optimization


def repl_smart_apos(m: re.Match) -> str:
    '''
    Translates "smart" apostrophe (right single quote ’ or prime ′) to apostrophe '.
    Keeps legit "‘...’" or "a′" as is.

    Basic quotes/apostrophies:

    >>> sub_smart_apos(repl_smart_apos, 'It’s me. It’s ‘you and me’.')
    "It's me. It's ‘you and me’."

    Trickier case (resolved using r'(?!s)'):

    >>> sub_smart_apos(repl_smart_apos, '‘It’s A’ ‘and’ it’s B.')
    "‘It's A’ ‘and’ it's B."

    Imperfect matching:

    >>> sub_smart_apos(repl_smart_apos,
    ...     'This isn‘t an apostrophe. ‘It’s an apostrophe.’ ‘This isn’t an apostrophe.'
    ...     )
    "This isn‘t an apostrophe. ‘It's an apostrophe.’ ‘This isn’t an apostrophe."

    Primes:

    >>> sub_smart_apos(repl_smart_apos, 'It′s an a′, it can′t be b′. Countries′ names.')
    "It's an a′, it can't be b′. Countries' names."
    '''

    in_quotes = m.group(1)  # inside paired single quotes
    return (
        # Keep outer quotes, replace inner right single quotes using translate():
        f'‘{in_quotes.translate(RSQUOTE2APOS)}’' if in_quotes is not None
        # Replace other right single quotes or primes found by regex:
        else '\''
        )


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Count word frequencies from a Wikipedia dump.'
        )

    default_processes = cpu_count() - 1
    parser.add_argument(
        '--processes', type=int, default=default_processes,
        help=(
            f'Number of processes to spawn (including wikiextractor, '
            f'default: {default_processes})'
            )
        )
    parser.add_argument(
        '--workers', type=int,
        help=(
            'Limit the number of the memory-hungry worker processes '
            '(not wikiextractor processes, default: no limit).'
            )
        )

    lang_group = parser.add_mutually_exclusive_group(required=False)
    lang_group.add_argument(
        '--zh', action='store_true', help='Chinese tokenization (jieba)'
        )
    lang_group.add_argument(
        '--ja', action='store_true',
        help='Japanese tokenization (MeCab, see --dicdir or --dictionary options)'
        )
    lang_group.add_argument(
        '--en', action='store_true',
        help=(
            'English tokenization (improved Penn Treebank tokenizer '
            'from nltk.tokenize.word_tokenize)'
            )
        )
    lang_group.add_argument(
        '--default', action='store_true', help='Default tokenization (regex)'
        )

    add_tagger_arg_group(parser, 'Options for --ja tokenization')

    default_group = parser.add_argument_group('Options for --en tokenization')
    default_group.add_argument(
        '--no-smart-apostrophe', action='store_false', dest='smart_apostrophe', help=(
            'Do not heuristically convert right single quote "’" to apostrophe "\'" '
            'before English tokenization'
            )
        )
    default_group.add_argument(
        '--relaxed', action='store_true', help=(
            'Count tokens containing at least one character in \\w.'
            )
        )

    parser.add_argument(
        '--min-docs', '-m', type=int, default=DEFAULT_MIN_DOCS,
        help=(
            f'Minimum documents for the word to be counted '
            f'(default: {DEFAULT_MIN_DOCS})'
            )
        )

    Storage.add_arg_group(parser, 'Compression options')

    parser.add_argument(
        '--output', '-o', type=str, required=True,
        help=(
            # % as %% to avoid formatting
            'Output filename for frequencies. If the placeholder "%%" is present, it '
            'is replaced with a string identifying the normalization. Otherwise, '
            'output only unnormalized data.'
            )
        )

    parser.add_argument(
        'dumps', type=str, nargs='+',
        help='Dumps for a Wikipedia language, e.g. dumps/*.bz2'
        )
    args = parser.parse_args()
    return args


def workers_d_p_per_worker(
    dumps: int,
    processes: int,
    max_workers: Optional[int] = None
    ) -> tuple[int, int, int]:
    '''
    Keep it simple by having a constant number of processes per worker and same (max)
    number of dumps per worker even though the allocation is suboptimal.

    If too little dumps/processes returns (0, 0, 0) => no multiprocessing.

    >>> workers_d_p_per_worker(1, 10)
    (0, 0, 0)
    >>> workers_d_p_per_worker(10, 3)
    (0, 0, 0)
    >>> workers_d_p_per_worker(10, 4)
    (2, 5, 2)
    >>> workers_d_p_per_worker(2, 4)
    (2, 1, 2)
    >>> workers_d_p_per_worker(2, 7)
    (2, 1, 3)
    '''
    workers     = min(dumps, processes // 2)
    if max_workers is not None and workers > max_workers:
        workers = max_workers
    if workers <= 1:
        return (0, 0, 0)

    d_per_w = ceil(dumps / workers)
    workers = ceil(dumps / d_per_w)   # actual workers may be less
    p_per_w = processes // workers

    assert p_per_w * workers <= processes
    assert p_per_w >= 2
    return (workers, d_per_w, p_per_w)


def main() -> None:
    args = parse()

    if args.en:
        from nltk.tokenize import word_tokenize  # type: ignore
        try:
            __ = word_tokenize('Split this!')
        except LookupError:
            sys.stderr.write(
                'It seems that "punkt" package for NLTK hasn\'t been '
                'downloaded yet. Will try to download.\n'
                )
            import nltk  # type: ignore
            nltk.download('punkt')

    storage         = Storage.from_args(args)
    freq_path: str  = args.output
    if not freq_path.endswith(storage.suffix):
        sys.stderr.write(
            f'Warning: Output path "{freq_path}" does not end '
            f'with the expected suffix "{storage.suffix}".\n'
            )

    dumps       = args.dumps
    n_dumps     = len(dumps)
    processes   = args.processes

    workers, w_n_dumps, w_proc = workers_d_p_per_worker(
        n_dumps,
        processes,
        args.workers
        )

    if workers == 0:
        counters = process(args, dumps, processes, show_progress=True)
    else:
        sys.stderr.write(
            f'Processing dump files in parallell with {workers} workers:\n'
            f' - {w_n_dumps} dump files per worker,\n'
            f' - {w_proc} processes per worker (including wikiextractor).\n\n'
            )
        w_dumps = [
            dumps[i:i + w_n_dumps]
            for i in range(0, n_dumps, w_n_dumps)
            ]
        assert len(w_dumps) == workers
        w_args = zip(
            repeat(args),
            w_dumps,
            repeat(w_proc)
            )
        with Pool(
            workers,
            maxtasksperchild=1  # free resources after task is done
            ) as pool:
            iter_counters = pool.imap_unordered(
                process_star,
                w_args,
                chunksize=1     # we do the chunking ourselves in `w_dumps`
                )
            counters = reduce(
                lambda c, d: c.merge(d),
                tqdm(
                    iterable=iter_counters,
                    desc='Merging results from workers',
                    total=workers
                    )
                )

    min_docs = args.min_docs
    if min_docs:
        counters.remove_less_than_min_docs(min_docs)

    counters.dump(
        freq_path,
        storage,
        cols=('word', 'count', 'documents')
        )

    counters.warnings_for_markup()


def process_star(
    args: tuple[argparse.Namespace, Sequence[str], int]
    ) -> WordCounterGroup:
    return process(*args)


def process(
    args: argparse.Namespace,
    # The following two parameters "override" args
    dumps: Sequence[str],
    processes: int,
    show_progress=False
    ) -> WordCounterGroup:
    if args.ja:
        tagger_parse = tagger_from_args(args).parse

        def tokenize(s):
            return tagger_parse(
                s.translate(NORMALIZE_FULLWIDTH_TILDE)
                ).split(' ')

    else:
        if args.zh:
            from jieba import cut as tokenize  # type: ignore
        elif args.en:
            from nltk.tokenize import word_tokenize  # type: ignore
            if args.smart_apostrophe:
                def tokenize(s):
                    return word_tokenize(
                        sub_smart_apos(repl_smart_apos, s)
                        )
            else:
                tokenize = word_tokenize
        else:
            # (implicitly) args.default
            tokenize = get_re_split().split

    re_word = (
        get_re_word(allow_start_end=WAVE_DASH) if args.ja else
        get_re_word() if (args.ja or args.zh) else
        get_re_word_relaxed() if args.en else
        None    # only filter out empty strings
        )

    # is_word = None => filter filters out false (empty strings):
    is_word = re_word.match if (re_word is not None) else None

    normalize       = '%' in args.output

    counters = WordCounterGroup(normalize=normalize, channels=False)
    # Optimization:
    c_add           = counters.add
    c_close_doc     = counters.close_doc

    cmd_path = which('wikiextractor')
    assert cmd_path is not None, (
        f'Cannot find the wikiextractor command. '
        f'Make sure to `pip install wikiextractor=={EXTRACTOR_VERSION}`.'
        )

    # Check wikiextractor version due to its quirkiness (see "quirky" below)

    cmd_v = subprocess.run(
        (cmd_path, '--version'), stdout=subprocess.PIPE,
        ).stdout.decode('utf-8').strip()
    if cmd_v != f'wikiextractor {EXTRACTOR_VERSION}':
        sys.stderr.write(
            f'Warning: Command found at {cmd_path} is not wikiextractor '
            f'{EXTRACTOR_VERSION} (instead {cmd_v}).\n'
            f'         This script has been tested only with wikiextractor '
            f'{EXTRACTOR_VERSION}, and may not work as expected versions.\n\n'
            )

    n_docs = 0
    iter_dumps = (
        tqdm(desc='Processing dump files', iterable=dumps) if show_progress
        else dumps
        )
    for dump_name in iter_dumps:
        cmd = (
            cmd_path,
            '--processes', str(processes - 1),
            '--no-templates',   # faster
            '-o', '-',          # output to stdout
            # quirky way of turning off html-safe output for EXTRACTOR_VERSION==3.0.6:
            '--html-safe', '',
            dump_name)
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
            assert p is not None, cmd
            assert p.stdout is not None, (cmd, p)
            with io.TextIOWrapper(p.stdout, encoding='utf-8') as p_out:
                in_score    = False    # inside <score>...</score> (ignored)
                maybe_score = None
                doc_open    = None
                for line in p_out:
                    # Document boundaries:
                    if line.startswith('<'):
                        # We assume docs are properly closed and opened:
                        if line.startswith('<doc '):
                            doc_open = line
                            continue
                        if line.startswith('</doc>'):
                            if in_score:
                                if maybe_score is not None:
                                    # maybe_score actually wasn't a score or both open
                                    # and close tags were missing => process all
                                    # supposed score lines:
                                    sys.stderr.write(
                                        f'Warning: Possible score without '
                                        f'<score>...</score> tags in:\n{doc_open}\n'
                                        f'Starts with:\n{maybe_score[0]}\n'
                                        )
                                    for line in maybe_score:
                                        words = list(filter(
                                            is_word,
                                            tokenize(remove_markup(line))
                                            ))
                                        c_add(words)
                                else:
                                    sys.stderr.write(
                                        f'Warning: Ignored lines upto the end of '
                                        f'article.  Missing </score> tag in:\n'
                                        f'{doc_open}\n'
                                        )
                                # also in case an actual <score> wasn't closed properly:
                                in_score = False
                            c_close_doc()
                            n_docs += 1
                            continue
                        # Continue processing if any tag other than "doc":

                    # Ignore <score>...</score> blocks:
                    if in_score:
                        m = search_score_close(line)
                        if m is not None:
                            in_score    = False
                            maybe_score = None
                            line = m.group(1)       # after </score>
                        else:
                            if maybe_score is not None:
                                # the lines will be processed if we don't find </score>
                                maybe_score.append(line)
                            continue                # ignore
                    else:
                        m  = search_score_open(line)
                        if m is not None:
                            before = m.group(1)       # before <score>
                            # Check if it isn't closed on the same line:
                            mc = search_score_close(line)
                            if mc is not None and mc.start() > m.start():
                                # keep in_score = False
                                line    = before + ' ' + m.group(1)  # + after </score>
                            else:
                                # Check if maybe instead of actual <score>
                                if m.group('maybe') is not None:
                                    maybe_score = [line]
                                in_score    = True
                                line        = before

                    words = list(filter(
                        is_word,
                        tokenize(remove_markup(line))
                        ))
                    c_add(words)

    counters.n_docs = n_docs

    return counters


if __name__ == '__main__':
    main()
