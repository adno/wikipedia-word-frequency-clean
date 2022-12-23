import sys
import io
import re
from shutil import which
import subprocess
import argparse
from tqdm import tqdm  # type: ignore
from ja_utils import get_re_word, get_re_split, get_re_word_relaxed, WAVE_DASH, \
    add_tagger_arg_group, tagger_from_args, NORMALIZE_FULLWIDTH_TILDE
from freq_utils import Storage, WordCounterGroup

DEFAULT_MIN_DOCS = 3


# The following markup is replaced with a space character.
# DO NOT keep content enclosed in <chem>.
# DO keep content enclosed in <ins>, <del>, <poem>
RE_MARKUP = re.compile(
    r'<br>|'
    r'<chem>[^<]*</chem>|'          # e.g. <chem>NH3 </chem>
    r'<ref [^>]+></ref>|'
    # e.g. <ref name="..."></ref>, <ref group="..." name="..."></ref>
    r'\b(row|col)span="[0-9]+"|'    # e.g. in '4||2||colspan="2"|', '!rowspan="2"|'
    r'(codice|formula)_[0-9]+|'     # e.g. 'DNAformula_20', '様にcodice_1 の'
    r'</?(ins|del)>|'               # e.g. <ins>text</ins>, <del>text</del>
    r'<(poem|q)( [^>]+)?>|</(poem|q)>'
    # e.g. <poem style="...">poem lines</poem> (or <q cite="夏目漱石『坊つちやん』">)
    )

# Do not keep the content enclosed in <score> (musical scores spanning multiple lines).
# (We do keep what's before and after.)
RE_SCORE_OPEN   = re.compile(r'(.*)<score [^>]+>')  # spans multiple lines
RE_SCORE_CLOSE  = re.compile(r'</score>(.*)')

# Within <ruby>:
# Keep untagged content or content tagged <rb> (the base text).
# Do not keep content in <rp> (ruby parents) or <rt> (ruby text, i.e. furigana)
RE_RUBY     = re.compile(r'<ruby( [^>]+)?>(?P<content>.*?)</ruby>')  # .*? non-greedy
RE_RUBY_DEL = re.compile(r'<rp>[^<]*</rp>|<rt( [^>]+)?>[^<]*</rt>|</?rb>')


def repl_ruby(m: re.Match) -> str:
    return RE_RUBY_DEL.sub('', m.group('content'))


def remove_markup(line: str) -> str:
    line = RE_MARKUP.sub(' ', line)
    return RE_RUBY.sub(repl_ruby, line)


# The right single quote '’' (but not the left single quote) is allowed to occur
# inside ‘...’ as long as it is surrounded by \w from both sides (\b’\b in the RE).
# E.g. ‘It’s an apostrophe.’ => “It’s an apostrophe.”
RE_SINGLE_QUOTE     = re.compile(r'‘(([^‘’]*\b’\b)*[^‘’]*)’')
REPL_DOUBLE_QUOTE   = r'“\1”'
RSQUOTE2APOS: dict[int, int] = {ord('’'): ord('\'')}


def smart_rsquote_to_apostrophe(s: str) -> str:
    '''
    Translates ‘...’ to “...”, and then ’ to '.

    >>> smart_rsquote_to_apostrophe('It’s me. It’s ‘you and me’.')
     "It's me. It's “you and me”.

    >>> smart_rsquote_to_apostrophe(
    ...     'This isn‘t an apostrophe. ‘It’s an apostrophe.’ ‘This isn’t an apostrophe.'
    ... )
    "This isn‘t an apostrophe. “It's an apostrophe.” “This isn”t an apostrophe."
    '''
    return RE_SINGLE_QUOTE.sub(REPL_DOUBLE_QUOTE, s).translate(RSQUOTE2APOS)


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Count word frequencies from a Wikipedia dump.'
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
        help='Minimum documents for the word to be counted',
        )

    Storage.add_arg_group(parser, 'Compression options')

    parser.add_argument(
        '--output', '-o', type=str,
        help=(
            'Output filename for frequencies. If the placeholder "%" is present, it '
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


def main() -> None:
    args = parse()

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
                    return word_tokenize(smart_rsquote_to_apostrophe(s))

            else:
                tokenize = word_tokenize
        else:
            assert args.default
            tokenize = get_re_split().split

    re_word = (
        get_re_word(allow_start_end=WAVE_DASH) if (args.ja or args.zh) else  # TODO zh
        (
            get_re_word_relaxed() if args.relaxed else
            get_re_word(allow_start_end='\'-')
            ) if args.en else
        None
        )

    if re_word is not None:
        def tokenize_words(s):
            return list(filter(re_word.match, tagger_parse(s).split(' ')))
    else:
        tokenize_words = tokenize

    storage         = Storage.from_args(args)
    freq_path: str  = args.output
    if not freq_path.endswith(storage.suffix):
        sys.stderr.write(
            f'Warning: Output path "{freq_path}" does not end '
            f'with the expected suffix "{storage.suffix}".\n'
            )
    normalize       = '%' in freq_path

    counters = WordCounterGroup(normalize=normalize, channels=False)

    doc_no = 0
    cmd_path = which('wikiextractor')
    for dump_name in tqdm(desc='Processing dump files', iterable=args.dumps):
        cmd = (cmd_path, '--no-templates', '-o', '-', dump_name)
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
            assert p is not None, cmd
            assert p.stdout is not None, (cmd, p)
            with io.TextIOWrapper(p.stdout, encoding='utf-8') as p_out:
                in_score = False    # inside <score>...</score> (ignored)
                for line in p_out:
                    # Document boundaries:
                    if line.startswith('<doc '):
                        # (in case <score> wasn't closed in previous doc):
                        in_score = False
                        doc_no += 1  # count only starts
                    elif line.startswith('</doc>'):
                        continue

                    # Ignore <score>...</score> blocks:
                    if in_score:
                        m = RE_SCORE_CLOSE.search(line)
                        if m is not None:
                            line = m.group(1)   # before <score>
                        else:
                            continue
                    m  = RE_SCORE_OPEN.search(line)
                    if m is not None:
                        in_score = True
                        line = m.group(1)       # after </score>

                    line = remove_markup(line)
                    words = tokenize_words(line)
                    counters.add(words, doc_no=doc_no)

    min_docs = args.min_docs
    if min_docs:
        counters.remove_less_than_min_docs(min_docs)

    counters.dump(
        freq_path,
        storage,
        cols=('word', 'count', 'documents'),
        n_docs=doc_no
        )


if __name__ == '__main__':
    main()
