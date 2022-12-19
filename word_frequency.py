import sys
import os
import io
import re
import subprocess
import argparse
from tqdm import tqdm
from collections import Counter, defaultdict
from ja_utils import get_re_word, get_re_split, WAVE_DASH, tagger_from_args, \
    NORMALIZE_FULLWIDTH_TILDE

DEFAULT_MIN_DOCS = 3

#PRE_TR = str.maketrans('–’', '-\'')
#RE_SPLIT_WORDS = re.compile(r'[^\w\-\']')
#is_word_re = re.compile(r'^\w.*\w$')        # Note: \w includes accented chars, CJK, etc.
#not_is_word_re = re.compile(r'.*\d.*')      # Note: \d includes decimals in many scripts, but not CJK

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
RE_RUBY         = re.compile(r'<ruby( [^>]+)?>(?P<content>.*?)</ruby>') # .*? non-greedy
RE_RUBY_DEL     = re.compile(r'<rp>[^<]*</rp>|<rt( [^>]+)?>[^<]*</rt>|</?rb>')

def repl_ruby(m):
    return RE_RUBY_DEL.sub('', m.group('content'))

def remove_markup(line):
    line = RE_MARKUP.sub(' ', line)
    return RE_RUBY.sub(repl_ruby, line)


def parse():
    parser = argparse.ArgumentParser(
        description='Count word frequencies from a Wikipedia dump.'
        )

    lang_group = parser.add_mutually_exclusive_group(required=False)
    lang_group.add_argument(
        '--zh', action='store_true', help='Chinese tokenization (jieba)'
        )
    lang_group.add_argument(
        '--ja', action='store_true',
        'Japanese tokenization (MeCab, see --dicdir or --dictionary options)'
        )
    lang_group.add_argument(
        '--default', action='store_true', help='Default tokenization (regex)'
        )

    dic_group = parser.add_mutually_exclusive_group('Options for --ja tokenization')
    dic_group.add_argument(
        '--dicdir', type=str, default=None,
        help='Dictionary directory for fugashi/MeCab.'
        )
    dic_group.add_argument(
        '--dictionary', '-D', choices=('unidic', 'unidic-lite'), default=None,
        help='Dictionary (installed as a Python package) for fugashi/MeCab'
        )
    default_group = parser.add_mutually_exclusive_group('Options for --default tokenization')
    default_group.add_argument(
        '--allow-apostrophe', action='store_true', help='Allow apostrophe in tokens'
        )
    default_group.add_argument(
        '--smart-apostrophe', action='store_true', help=(
            'Heuristically convert right single quote "’" to apostrophe "\'" '
            '(to be used in conjunction with --allow-apostrophe)'
            )
    default_group.add_argument(
        '--allow-hyphen', action='store_true', help='Allow hyphen in tokens'
        )

    parser.add_argument(
        '--nfkc', action='store_true', help='Normalize to NFKC'
        )
    parser.add_argument(
        '--lower', action='store_true', help='Lowercase'
        )


    parser.add_argument('--min-docs', '-m', type=int, help='Minimum documents for the word to be counted.', default=DEFAULT_MIN_DOCS)
    parser.add_argument('dumps', type=str, nargs='+', help='Bzipped dumps for a Wikipedia language, e.g. dumps/*.bz2')
    args = parser.parse_args()
    return args


def main():
    args = parse()

    split_line      = lambda line: filter(None, RE_SPLIT_WORDS.split(line))


    # Japanese word segmentation does not recognize some words if lower-cased (e.g. Tシャツ).
    # Therefore we normalize AFTER segmentation.

    pre_normalize = not args.no_normalization
    post_normalize = False

    if args.ja_dicdir is not None:
        # Import fugashi only if processing Japanese:
        from ja_utils import LCASE_FW2HW, fugashi_tagger
        tagger = fugashi_tagger(args.ja_dicdir or None) # pass None of arg is '' (const='')
        def split_line(s):
            return tagger.parse(s).split(' ')
        pre_normalize = False
        post_normalize = not args.no_normalization
    elif args.zh:
        import jieba
        split_line = jieba.cut
        pre_normalize = False
        post_normalize = not args.no_normalization
    # elif args.auto: pass

    delimiter=' '
    if args.tab_separated:
        delimiter = '\t'
    elif args.delim is not None:
        delimiter = args.delim

    min_docs                = args.min_docs
    output_doc_frequency    = args.doc_frequency
    output_total            = args.total | output_doc_frequency

    # collect data

    word_count: Counter[str, int] = Counter()
    word_docs: dict[str, set[int]] = defaultdict(set)

    doc_no = 0
    for dump_name in tqdm(desc='Processing dump files', iterable=dumps):
        with subprocess.Popen(
            f'wikiextractor --no-templates -o - {dump_name}',
            stdout=subprocess.PIPE, shell=True
            ) as proc, \
            io.TextIOWrapper(proc.stdout, encoding='utf-8') as proc_out:
            in_score = False    # inside <score>...</score> (ignored)

            for line in proc_out:
                # Document boundaries:
                if line.startswith(b'<doc '):
                    in_score = False            # (just in case <score> wasn't closed in the previous doc)
                    doc_no += 1                 # count only starts
                elif line.startswith(b'</doc>'):
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

                if pre_normalize:
                    line = line.translate(PRE_TR).lower()
                for word in split_line(line):
                    if is_word_re.match(word) and not not_is_word_re.match(word):
                        if post_normalize:
                            word = word.lower().translate(LCASE_FW2HW)
                        word_count[word] += 1
                        word_docs[word].add(doc_no)

    # remove words used in < min_docs

    for word, docs in word_docs.items():
        if len(docs) < min_docs:
            del word_count[word]

    # save raw data

    line_format = '%%s%s%%d%s%%d'%(delimiter, delimiter) if output_doc_frequency else ('%%s%s%%d'%delimiter)

    words = list(word_count.keys())
    words.sort(key=lambda w: word_count[w], reverse=True)
    total_uses = 0
    if output_doc_frequency:
        for word in words:
            wu = word_count[word]
            total_uses += wu
            print(line_format % (word, wu, len(word_docs[word])))
    else:
        for word in words:
            wu = word_count[word]
            total_uses += wu
            print(line_format % (word, wu))

    if output_total:
        if output_doc_frequency:
            print(line_format%('[TOTAL]', total_uses, doc_no))
        else:
            print(line_format%('[TOTAL]', total_uses))

if __name__ == '__main__':
    main()
