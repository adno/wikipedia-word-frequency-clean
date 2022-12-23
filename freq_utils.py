'''
Word frequency counting for `tubelex` and `wikipedia-word-frequency-clean`.
'''

from typing import Optional, Union, NamedTuple, TextIO
from unicodedata import normalize as unicode_normalize
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from enum import Enum
from zipfile import ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA
import gzip
import bz2
import lzma
import argparse

NORMALIZED_SUFFIX_FNS = (
    (False, '', None),
    (True, '-lower', lambda w: w.lower()),
    (True, '-nfkc', lambda w: unicode_normalize('NFKC', w)),
    (True, '-nfkc-lower', lambda w: unicode_normalize('NFKC', w).lower())
    )
TOTAL_LABEL = '[TOTAL]'


class Storage(Enum):
    PLAIN = (None, open, '')
    DEFLATE = (ZIP_DEFLATED, gzip.open, '.gz')
    BZIP2 = (ZIP_BZIP2, bz2.open, '.bz2')
    LZMA = (ZIP_LZMA, lzma.open, '.xz')

    def __init__(self, zip_compression, open_fn, suffix):
        self.zip_compression    = zip_compression
        self.open               = open_fn
        self.suffix             = suffix

    @staticmethod
    def from_args(args: argparse.Namespace) -> 'Storage':
        return (
            Storage.DEFLATE if args.deflate else
            Storage.BZIP2 if args.bzip2 else
            Storage.LZMA if args.lzma else
            Storage.PLAIN
            )

    @staticmethod
    def add_arg_group(
        parser: argparse.ArgumentParser,
        title: Optional[str] = None,
        zip_suffix: bool = False
        ):
        titled_group = parser.add_argument_group(title=title)
        arg_group = titled_group.add_mutually_exclusive_group()
        opt_zip_s = '.zip/' if zip_suffix else ''
        arg_group.add_argument(
            '--deflate', '--zip', '-z', action='store_true',
            help=f'Store data deflated ({opt_zip_s}.gz)'
            )
        arg_group.add_argument(
            '--bzip2', '-j', action='store_true',
            help=f'Store data using Bzip2 ({opt_zip_s}.bz2)'
            )
        arg_group.add_argument(
            '--lzma', '--xz', '-x', action='store_true',
            help=f'Store data using LZMA ({opt_zip_s}.xz)'
            )


class WordCounter(NamedTuple):
    word_count: Counter[str]
    word_docs: dict[str, set[int]]                              # documents or videos
    word_channels: Optional[dict[str, set[Union[int, str]]]]    # for tubelex (YouTube)

    @staticmethod
    def new(channels: bool = False) -> 'WordCounter':
        return WordCounter(
            word_count=Counter(),
            word_docs=defaultdict(set),
            word_channels=defaultdict(set) if channels else None
            )

    def add(
        self,
        words: Iterable[str],
        doc_no: int,
        channel_id: Optional[Union[int, str]] = None
        ):
        assert (channel_id is None) == (self.word_channels is None), (
            channel_id, self.word_channels
            )
        for w in words:
            self.word_count[w] += 1
            self.word_docs[w].add(doc_no)
            if self.word_channels is not None:
                self.word_channels[w].add(channel_id)   # type: ignore

    def remove_less_than_min_docs(self, min_docs: int):
        for word, docs in self.word_docs.items():
            if len(docs) < min_docs:
                del self.word_count[word]

    def remove_less_than_min_channels(self, min_channels: int):
        assert self.word_channels is not None
        for word, channels in self.word_channels.items():
            if len(channels) < min_channels:
                del self.word_count[word]

    def dump(
        self,
        f: TextIO,
        cols: Sequence[str],
        totals: Sequence[int]
        ):
        w_count     = self.word_count
        w_docs      = self.word_docs
        w_channels  = self.word_channels
        n_numbers   = 2 if w_channels is None else 3
        assert len(cols) == 1 + len(totals), (cols, totals)  # 1 is for TOTAL_LABEL
        assert len(totals) == n_numbers, (totals, n_numbers)

        line_format = '%s' + ('\t%d' * n_numbers) + '\n'

        words = sorted(w_count, key=w_count.__getitem__, reverse=True)

        f.write('\t'.join(cols) + '\n')
        if w_channels is None:
            for word in words:
                f.write(line_format % (
                        word,  w_count[word], len(w_docs[word])
                        ))
        else:
            for word in words:
                f.write(line_format % (
                        word,  w_count[word], len(w_docs[word]), len(w_channels[word])
                        ))

        f.write(line_format % (
            TOTAL_LABEL, *totals
            ))


class WordCounterGroup(dict[str, WordCounter]):
    __slots__ = ('n_words')
    n_words: int

    def __init__(self, normalize: bool, channels: bool = False):
        super().__init__((
            (suffix, WordCounter.new(channels=channels))
            for normalized, suffix, __ in NORMALIZED_SUFFIX_FNS
            if normalize or not normalized
            ))
        self.n_words = 0

    def add(
        self,
        words: Sequence[str],
        doc_no: int,
        channel_id: Optional[Union[int, str]] = None
        ):
        for __, suffix, norm_fn in NORMALIZED_SUFFIX_FNS:
            c = self.get(suffix)
            if c is not None:
                c.add(
                    map(norm_fn, words) if (norm_fn is not None) else words,
                    doc_no=doc_no,
                    channel_id=channel_id
                    )
        self.n_words += len(words)

    def remove_less_than_min_docs(self, min_docs: int):
        for c in self.values():
            c.remove_less_than_min_docs(min_docs)

    def remove_less_than_min_channels(self, min_channels: int):
        for c in self.values():
            c.remove_less_than_min_docs(min_channels)

    def dump(
        self,
        path_pattern: str,
        storage: Storage,
        cols: Sequence[str],
        n_docs: int,
        n_channels: Optional[int] = None
        ):
        totals = [self.n_words, n_docs]
        if n_channels is not None:
            totals.append(n_channels)
        for suffix, c in self.items():
            with storage.open(
                path_pattern.replace('%', suffix),  # no effect if not do_norm (no '%')
                'wt'
                ) as f:
                c.dump(f, cols, totals)
