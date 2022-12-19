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


def get_re_word(allow_start_end: str = '') -> re.Pattern:
    '''
    Match words of len>=1. No decimal digits (\\d) at any position.
    First and last character must be word-forming (\\w), i.e. alphabet, CJK, etc.

    Note: \\w includes accented chars, CJK, etc.
    \\d are decimals in many scripts, but not CJK.

    Use `allow_start_end` to allow characters other than \\w, such as hyphen,
    apostrophe (English) or wave dash (Japanese) to appear as the first or last
    characters. (Note: does not work for adding digits.)

    Useful both for space-separated languages (segmented with regex) and languages
    requiring more complex segmentation (Chinese, Japanese).
    '''

    _assert_safe_for_re_range(allow_start_end)

    return re.compile(
        rf'^(?!\d)[\w{allow_start_end}]([^\d]*[\w{allow_start_end}])?(?<!\d)$'
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

# TODO Unused since we do full NFKC normalization.
# NORMALIZE_FULLWIDTH_LCASE: dict[int, int] = dict(zip(
#     range(ord('ａ'), ord('ｚ') + 1),  # fullwidth a-z
#     range(ord('a'), ord('z') + 1)  # half-width a-z
#     ))  # Used with str.translate() after lowercasing

NORMALIZE_FULLWIDTH_TILDE: dict[int, int] = {
    0xFF5E: 0x301C  # fullwidth tilde '～' (common typo) => wave dash '〜'
    }


def fugashi_tagger(dicdir: Optional[str]) -> fugashi.GenericTagger:
    if dicdir is None:
        return fugashi.Tagger('-O wakati')  # -d/-r supplied automatically
    # GenericTagger: we do not supply wrapper (not needed wor -O wakati)
    mecabrc = os.path.join(dicdir, 'mecabrc')
    return fugashi.GenericTagger(f'-O wakati -d {dicdir} -r {mecabrc}')


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