# About wikipedia-word-frequency-clean

This project provides word frequency lists generated from cleaned-up Wikipedia dumps for the following languages:

- Chinese (traditional)
- Czech
- English
- French
- German
- Italian
- Japanese
- Portuguese
- Russian
- Spanish

Furthermore, the project provides a script for generating the lists that can be applied to other Wikipedia languages.

For each word, we count:
- number of occurrences,
- number of documents (Wikipedia articles).

Words occurring in less than 3 articles are not included. The list is sorted by the number of occurrences. The data is tab-separated with a header, and the file is compressed with LZMA2 (`xz`).

**Important:** The last row labeled `[TOTAL]` lists the **total numbers** of tokens and articles, and thus may **require special handling**. Also, note that the totals are not sums of the previous rows' values.

## How is this different from [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency)?

We strive for data that is cleaner (not containing spurious “words” such as `br` or `colspan`), and linguistically meaningful (correctly segmented, with consistent criteria for inclusion in the list). Here are the specific differences:

1. **Cleanup:** We remove HTML tags such as (`<br>`, `<ref>`, etc.), table formatting (`colspan`, `rowspan`), placeholders for formulas and code (`formula_…`, `codice_…`) or ruby (furigana).

2. **Tokenization:** We tokenize **Japanese** and **Chinese**, see [About mutations](#about-mutations). This is necessary, because these languages do not separate words with spaces. (The [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency) script, simply extracts and counts any contiguous chunks of characters, which can range from a word to a whole sentence.)

We tokenize **other languages** using a regular expression for orthographic words, consistently treating hyphen `-` and apostrophe `'` as punctuation that cannot occur inside a word. (The wikipedia-word-frequency script allows these characters except start or end of word, thus allowing `women's` but excluding `mens'`. It also blindly converts en-dashes to hyphens, e.g. tokenizing `New York–based` as `New` and `York-based`, and right single quotation marks to apostrophes, resulting into further discrepancies.)

For **English**, in addition to the default regex tokenization, we also provide the Penn Treebank tokenization (e.g. `can't` segmented as `ca` and `n't`). In this case, apostrophes are allowed, and we also do a smart conversion of right single quotation marks to apostrophes (to distinguish the intended apostrophe in `can’t` from the actual quotation mark in `‘tuna can’`).

3. **Inclusion criteria:** We count [words](#what-is-considered-a-word) of any length, including one-character words (such as “I” or “a” in English or “茶” in Japanese or Chinese, which aren't counted by wikipedia-word-frequency).

4. **Normalization:** For all languages, we provide [mutations](#about-mutations) that are lowercased and/or normalized to NFKC.

## About mutations

For each language we provide several mutations.

* **All languages** have the following mutations distinguished by the filename suffixes:
	- `*.tsv.xz`: no normalization,
	- `*-lower.tsv.xz`: no normalization, lowercased,
	- `*-nfkc.tsv.xz`: NFKC normalization
	- `*-nfkc-lower.tsv.xz`: NFKC normalization, lowercased

  In addition to that, there are two variants of English and Japanese tokenization:

* **English:**
    - regex tokenization (same as for Czech, French, etc.)
    - filename contains `-penn`: improved Penn Treebank tokenization from `nltk.tokenize.word_tokenize`

* **Japanese:** We do the same processing and provide the same mutations for Japanese [as in TUBELEX-JA](https://github.com/adno/tubelex#about-mutations):
	- Unidic Lite tokenization
	- filename contains `-310`: Unidic 3.1.0 tokenization

**Chinese** is tokenized using the `jieba` tokenizer.

## What is considered a word?

1. **English with Penn Treebank tokenization**: Tokens that fulfil the following conditions:
  - do not contain digits
  - start with a word character (\w), apostrophe, or dash.
  - end with a word character (\w), apostrophe, dash, or period.

  E.g. `a`, `o'clock`, `'coz`, `pre-/post-`, `U.S.A.`, but not `42`, `R2D2`, `...` or `.`.

2. Japanese and Chinese: Tokens that fulfil the following conditions:
  - do not contain digits (characters, such `一二三` are not considered digits),
  - start and end with a word character (\w) or wave dash (〜).

3. Other languages and English with the default regex tokenization:
  - tokens that consist of word characters (\w) except digits.
  
The default regex tokenization considers all non-word characters (\W, i.e. not \w) word separators. Therefore, while in English with Penn Treebank tokenization some tokens (e.g. `R2D2`) are excluded, with the regex tokenization, tokens that would have to be excluded do not occur in the first place (e.g. `R2D2` is tokenized as `R` and `D`).

# Usage

TBD

# Results

TBD

# Further work and similar lists

The word lists contain only the surface forms of the words (segments). For many purposes, lemmas, POS and other information would be more useful. We plan to add further processing later.

You may also like [TUBELEX-JA](https://github.com/adno/tubelex/),a large word list based on Japanese subtitles for YouTube videos, which is processed in a similar way.
