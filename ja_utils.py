'''
Japanese language processing for `tubelex` and `wikipedia-word-frequency-clean`.
'''

import fugashi  # type: ignore
import os
from typing import Optional
import argparse
import re


# Word matching (not just) for Japanese


def _assert_safe_for_re_range(s: str) -> None:
    '''
    Sanity checks before we insert `s` it at the end of a regex range [...s].
    '''
    assert len(s) == len(set(s))
    assert ']' not in s
    assert '\\' not in s
    assert ('-' not in s) or s.endswith('-')


def get_re_word(
    allow_start_end: str = '',
    allow_end: str = ''
    ) -> re.Pattern:
    '''
    Match words of len>=1. No decimal digits (\\d) at any position.
    First and last character must be word-forming (\\w), i.e. alphabet, CJK, etc.

    Note: \\w includes accented chars, CJK, etc.
    \\d are decimals in many scripts, but not CJK.

    Use `allow_start_end` to allow characters other than \\w, such as hyphen,
    apostrophe (English) or wave dash (Japanese) to appear as the first or last
    characters. (Note: does not work for adding digits.)

    Use `allow_end` to allow characters to appear as last characters of a word longer
    than a single character.

    Useful both for space-separated languages (segmented with regex) and languages
    requiring more complex segmentation (Chinese, Japanese).
    '''

    _assert_safe_for_re_range(allow_start_end)
    _assert_safe_for_re_range(allow_end)
    assert '-' not in allow_end

    return re.compile(
        rf'^(?!\d)[\w{allow_start_end}]'
        rf'([^\d]*[\w{allow_end}{allow_start_end}])?(?<!\d)$'
        )


def get_re_word_relaxed() -> re.Pattern:
    '''
    All non-digit ([^\\d]), at least one word-forming ([\\w]) character.
    '''
    return re.compile(
        r'^([^\d]*(?!\d)[\w][^\d]*)$'
        )


def get_re_split(no_split: str = '') -> re.Pattern:
    '''
    Match non-word sequences to split words. Such sequences may consist of:
    - characters not in \\w or in `no_split`
    - characters in \\d

    For languages that can be segmented with a regex (not Chinese or Japanase).
    Also see `get_re_word()`.
    '''
    _assert_safe_for_re_range(no_split)

    # We need a non-capturing group '(?:...)' for split() to use the whole regex
    return re.compile(rf'(?:[^\w{no_split}]|\d)+')


WAVE_DASH   = '\u301C'  # 〜 may look like fullwidth tilde ～
EN_DASH     = '\u2013'  # – may look like hyphen -


# Examples (test):
_re_word = get_re_word()
_re_split = get_re_split()
assert all(_re_word.fullmatch(w) for w in ['a', '亀', 'コアラ', 'Pú', 'A/B', 'bla-bla'])
assert not any(
    _re_word.match(w) for w in ['', '1', 'a1', '1a', 'C3PIO', '/', '-', 'あ〜']
    )
assert get_re_word(allow_start_end=WAVE_DASH).match('あ〜')
assert (
    _re_split.split('a.b  cč5dď-eé\'ff1+2*3.5koala') ==
    ['a', 'b', 'cč', 'dď', 'eé', 'ff', 'koala']
    )


NORMALIZE_FULLWIDTH_TILDE: dict[int, int] = {
    0xFF5E: 0x301C  # fullwidth tilde '～' (common typo) => wave dash '〜'
    }


def fugashi_tagger(dicdir: Optional[str]) -> fugashi.GenericTagger:
    if dicdir is None:
        return fugashi.Tagger('-O wakati')  # -d/-r supplied automatically
    # GenericTagger: we do not supply wrapper (not needed wor -O wakati)
    mecabrc = os.path.join(dicdir, 'mecabrc')
    return fugashi.GenericTagger(f'-O wakati -d {dicdir} -r {mecabrc}')


def add_tagger_arg_group(
    parser: argparse.ArgumentParser,
    title: Optional[str] = None
    ):
    titled_group = parser.add_argument_group(title=title)
    dic_group = titled_group.add_mutually_exclusive_group()
    dic_group.add_argument(
        '--dicdir', type=str, default=None,
        help='Dictionary directory for fugashi/MeCab.'
        )
    dic_group.add_argument(
        '--dictionary', '-D', choices=('unidic', 'unidic-lite'), default=None,
        help='Dictionary (installed as a Python package) for fugashi/MeCab.'
        )


def tagger_from_args(args: argparse.Namespace) -> fugashi.GenericTagger:
    # We always specify dicdir EXPLICITLY
    if args.dicdir is not None:
        dicdir = args.dicdir
    else:
        if args.dictionary == 'unidic':
            import unidic  # type: ignore
            dicdir = unidic.DICDIR
        else:
            assert args.dictionary is None or args.dictionary == 'unidic-lite'
            import unidic_lite  # type: ignore
            dicdir = unidic_lite.DICDIR
    return fugashi_tagger(dicdir)


# Normalizng English QUOTES/APOSTROPHES:

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
