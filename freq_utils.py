'''
Word frequency counting for `tubelex` and `wikipedia-word-frequency-clean`.
'''

from typing import Optional, Union, TextIO
from unicodedata import normalize as unicode_normalize
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from enum import Enum
from zipfile import ZIP_DEFLATED, ZIP_BZIP2, ZIP_LZMA
import gzip
import bz2
import lzma
import argparse
import sys

NORMALIZED_SUFFIX_FNS = (
    (False, '', None),
    (True, '-lower', lambda w: w.lower()),
    (True, '-nfkc', lambda w: unicode_normalize('NFKC', w)),
    (True, '-nfkc-lower', lambda w: unicode_normalize('NFKC', w).lower())
    )
TOTAL_LABEL = '[TOTAL]'

DEFAULT_MARKUP = (
    # GT (lowercased: gt) is actually quite common in Japanese wikipedia:-)
    # BR (lcased: br) "BR Deutschland" in German
    'lt', 'br', 'ref', 'onlyinclude', 'colspan', 'align', 'ruby',
    # 'del' is very common in Italian and Spanish => all European wikipedias
    # 'font' is a common word in French
    'https'
    )

DEFAULT_TOP_N = 6000


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


class WordCounter:
    '''
    The lifecycle of a WordCounter object:

    1. For each document:
      - add words with add() (possibly calling it several times)
      - close document with close_doc()

    2. Merge/adjust and issue output:
      - merge()
      - remove_less_than_min_docs()
      - remove_less_than_min_channels()
      - warnings_for_markup()
      - dump()

    >>> c = WordCounter()
    >>> c.add('abcdefgh')
    >>> c.close_doc()
    >>> c.add('abcd')
    >>> c.close_doc()
    >>> sum(c.word_count.values())
    12
    >>> d = WordCounter()
    >>> d.add('abcdabcdijklijkl')
    >>> d.close_doc()
    >>> sum(d.word_count.values())
    16
    >>> m = c.merge(d)
    >>> c is m
    True
    >>> sum(m.word_count.values())
    28
    >>> m.word_count['a']
    4
    >>> m.word_count['e']
    1
    >>> m.word_count['i']
    2
    >>> m.word_docn['a']
    3
    >>> m.word_docn['e']
    1
    >>> m.word_docn['i']
    1
    >>> m.remove_less_than_min_docs(3)
    >>> ''.join(sorted(m.word_count.keys()))
    'abcd'

    Can be pickled (and implements __eq__):

    >>> import pickle
    >>> p = pickle.loads(pickle.dumps(m))
    >>> p == m
    True
    '''
    __slots__ = ('word_count', 'word_docn', 'word_channels', 'doc_words')
    word_count: Counter[str]
    word_docn: Counter[str]                                     # documents or videos
    word_channels: Optional[dict[str, set[Union[int, str]]]]    # for tubelex (YouTube)
    doc_words: set[str]                                         # words in current doc

    def __init__(self, channels: bool = False):
        super().__init__()
        self.word_count     = Counter()
        self.word_docn      = Counter()
        self.word_channels  = defaultdict(set) if channels else None
        self.doc_words      = set()

    def __eq__(self, other):
        return (
            self.word_count == other.word_count and
            self.word_docn == other.word_docn and
            self.word_channels == other.word_channels and
            self.doc_words == self.doc_words
            )

    def add(
        self,
        words: Iterable[str],
        channel_id: Optional[Union[int, str]] = None
        ):
        assert (channel_id is None) == (self.word_channels is None), (
            channel_id, self.word_channels
            )
        for w in words:
            self.word_count[w] += 1
            self.doc_words.add(w)
            if self.word_channels is not None:
                self.word_channels[w].add(channel_id)  # type: ignore

    def close_doc(self):
        self.word_docn.update(self.doc_words)
        self.doc_words = set()

    def remove_less_than_min_docs(self, min_docs: int):
        assert not self.doc_words, 'Missing `close_doc()`?'
        for word, docn in self.word_docn.items():
            if docn < min_docs:
                del self.word_count[word]

    def remove_less_than_min_channels(self, min_channels: int):
        assert self.word_channels is not None
        for word, channels in self.word_channels.items():
            if len(channels) < min_channels:
                del self.word_count[word]

    def warnings_for_markup(
        self,
        top_n: int = DEFAULT_TOP_N,
        markup: Iterable[str] = DEFAULT_MARKUP,
        suffix: str = ''
        ):
        top_words   = set(w for w, __ in self.word_count.most_common(top_n))
        suffix_str  = f', in *{suffix}' if suffix else ''
        for w in top_words.intersection(markup):
            sys.stdout.write(
                f'Warning: Possible markup "{w}" found among top {top_n} words with '
                f'frequency {self.word_count[w]}{suffix_str}.\n'
                )

    def merge(self, other: 'WordCounter') -> 'WordCounter':
        assert not self.doc_words, 'Missing `self.close_doc()`?'
        assert not other.doc_words, 'Missing `other.close_doc()`?'

        self.word_count.update(other.word_count)

        # Documents have unique ids, we just add the counts:

        wdn = self.word_docn
        owd = other.word_docn
        for w, od in owd.items():
            wdn[w] += od

        # Merge sets of channels:

        wc = self.word_channels
        owc = other.word_channels
        if wc is not None:
            assert owc is not None
            for w, oc in owc.items():
                c = wc.get(w)
                if c is None:
                    wc[w] = oc
                else:
                    c.update(oc)
        else:
            assert owc is None

        return self

    def dump(
        self,
        f: TextIO,
        cols: Sequence[str],
        totals: Sequence[int],
        sep: str = '\t'
        ):
        '''
        >>> c = WordCounter()
        >>> c.add('deabcdabcaba')
        >>> c.close_doc()
        >>> c.add('abc')
        >>> c.close_doc()
        >>> c.dump(sys.stdout, ('word', 'count', 'documents'), (100, 200), sep=' ')
        word count documents
        a 5 2
        b 4 2
        c 3 2
        d 2 1
        e 1 1
        [TOTAL] 100 200
        '''
        assert not self.doc_words, 'Missing `close_doc()`?'

        w_count     = self.word_count
        w_docn      = self.word_docn
        w_channels  = self.word_channels
        n_numbers   = 2 if w_channels is None else 3
        assert len(cols) == 1 + len(totals), (cols, totals)  # 1 is for TOTAL_LABEL
        assert len(totals) == n_numbers, (totals, n_numbers)

        line_format = '%s' + (f'{sep}%d' * n_numbers) + '\n'

        words = sorted(w_count, key=w_count.__getitem__, reverse=True)

        f.write(sep.join(cols) + '\n')
        if w_channels is None:
            for word in words:
                f.write(line_format % (
                        word,  w_count[word], w_docn[word]
                        ))
        else:
            for word in words:
                f.write(line_format % (
                        word,  w_count[word], w_docn[word], len(w_channels[word])
                        ))

        f.write(line_format % (
            TOTAL_LABEL, *totals
            ))


class WordCounterGroup(dict[str, WordCounter]):
    __slots__ = ('n_words', 'n_docs')
    n_words: int
    n_docs: int

    def __init__(self, normalize: bool, channels: bool = False):
        super().__init__((
            (suffix, WordCounter(channels=channels))
            for normalized, suffix, __ in NORMALIZED_SUFFIX_FNS
            if normalize or not normalized
            ))
        self.n_words = 0
        self.n_docs = 0

    def add(
        self,
        words: Sequence[str],
        channel_id: Optional[Union[int, str]] = None
        ):
        for __, suffix, norm_fn in NORMALIZED_SUFFIX_FNS:
            c = self.get(suffix)
            if c is not None:
                c.add(
                    map(norm_fn, words) if (norm_fn is not None) else words,
                    channel_id=channel_id
                    )
        self.n_words += len(words)

    def close_doc(self):
        for c in self.values():
            c.close_doc()

    def remove_less_than_min_docs(self, min_docs: int):
        for c in self.values():
            c.remove_less_than_min_docs(min_docs)

    def remove_less_than_min_channels(self, min_channels: int):
        for c in self.values():
            c.remove_less_than_min_docs(min_channels)

    def warnings_for_markup(
        self,
        top_n: int = DEFAULT_TOP_N,
        markup: Iterable[str] = DEFAULT_MARKUP
        ):
        for suffix, c in self.items():
            c.warnings_for_markup(top_n, markup, suffix)

    def merge(self, other: 'WordCounterGroup') -> 'WordCounterGroup':
        for suffix, c in self.items():
            c.merge(other[suffix])
        self.n_words += other.n_words
        self.n_docs += other.n_docs

        return self

    def dump(
        self,
        path_pattern: str,
        storage: Storage,
        cols: Sequence[str],
        n_docs: Optional[int] = None,
        n_channels: Optional[int] = None
        ):
        if n_docs is None:
            n_docs = self.n_docs
        totals = [self.n_words, n_docs]
        if n_channels is not None:
            totals.append(n_channels)
        for suffix, c in self.items():
            with storage.open(
                path_pattern.replace('%', suffix),  # no effect if not do_norm (no '%')
                'wt'
                ) as f:
                c.dump(f, cols, totals)
