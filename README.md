# About wikipedia-word-frequency-clean

This project provides word frequency lists generated from cleaned-up Wikipedia dumps for several languages. The following table shows the number of **words** (types) for each language and [mutation](#about-mutations) (2nd–5th column) with **links to the list files**, as well as the number of **tokens** and **articles** (6th and 7th column).

| Language / Mutation | no&nbsp;norm. | no&nbsp;norm., lowercased | NFKC&nbsp;norm. | NFKC&nbsp;norm., lowercased | #tokens | #articles |
|:-------- | -------------:| -------------------------:| ---------------:| ---------------------------:|  -------:| ---------:|
| Czech<sub>regex</sub> | [866,695](results/cswiki-frequency-20221020.tsv.xz) | [772,835](results/cswiki-frequency-20221020-lower.tsv.xz) | [866,679](results/cswiki-frequency-20221020-nfkc.tsv.xz) | [772,818](results/cswiki-frequency-20221020-nfkc-lower.tsv.xz) | 137,569,192 | 832,966 |
| English<sub>regex</sub> | [2,420,793](results/enwiki-frequency-20221020.tsv.xz) | [2,163,083](results/enwiki-frequency-20221020-lower.tsv.xz) | [2,420,581](results/enwiki-frequency-20221020-nfkc.tsv.xz) | [2,162,842](results/enwiki-frequency-20221020-nfkc-lower.tsv.xz) | 2,492,809,074 | 16,699,989 |
| English<sub>Penn</sub> | [2,974,622](results/enwiki-frequency-20221020-penn.tsv.xz) | [2,695,448](results/enwiki-frequency-20221020-penn-lower.tsv.xz) | [2,974,517](results/enwiki-frequency-20221020-penn-nfkc.tsv.xz) | [2,695,337](results/enwiki-frequency-20221020-penn-nfkc-lower.tsv.xz) | 2,478,149,621 | 16,699,990 |
| English<sub>Penn, relaxed</sub> | [2,989,647](results/enwiki-frequency-20221020-pennr.tsv.xz) | [2,710,672](results/enwiki-frequency-20221020-pennr-lower.tsv.xz) | [2,989,575](results/enwiki-frequency-20221020-pennr-nfkc.tsv.xz) | [2,710,590](results/enwiki-frequency-20221020-pennr-nfkc-lower.tsv.xz) | 2,445,758,213 | 16,699,990 |
| French<sub>regex</sub> | [1,188,277](results/frwiki-frequency-20221020.tsv.xz) | [1,061,410](results/frwiki-frequency-20221020-lower.tsv.xz) | [1,188,080](results/frwiki-frequency-20221020-nfkc.tsv.xz) | [1,061,170](results/frwiki-frequency-20221020-nfkc-lower.tsv.xz) | 843,020,600 | 4,108,861 |
| German<sub>regex</sub> | [2,692,031](results/dewiki-frequency-20221020.tsv.xz) | [2,557,190](results/dewiki-frequency-20221020-lower.tsv.xz) | [2,691,955](results/dewiki-frequency-20221020-nfkc.tsv.xz) | [2,557,086](results/dewiki-frequency-20221020-nfkc-lower.tsv.xz) | 893,569,896 | 4,455,795 |
| Italian<sub>regex</sub> | [960,295](results/itwiki-frequency-20221020.tsv.xz) | [852,136](results/itwiki-frequency-20221020-lower.tsv.xz) | [960,206](results/itwiki-frequency-20221020-nfkc.tsv.xz) | [852,045](results/itwiki-frequency-20221020-nfkc-lower.tsv.xz) | 522,851,171 | 2,783,290 |
| Japanese<sub>Unidic Lite</sub> | [549,880](results/jawiki-frequency-20221020.tsv.xz) | [522,707](results/jawiki-frequency-20221020-lower.tsv.xz) | [549,494](results/jawiki-frequency-20221020-nfkc.tsv.xz) | [522,328](results/jawiki-frequency-20221020-nfkc-lower.tsv.xz) | 610,522,458 | 2,177,257 |
| Japanese<sub>Unidic 3.1.0</sub> | [561,344](results/jawiki-frequency-20221020-310.tsv.xz) | [535,841](results/jawiki-frequency-20221020-310-lower.tsv.xz) | [560,953](results/jawiki-frequency-20221020-310-nfkc.tsv.xz) | [535,456](results/jawiki-frequency-20221020-310-nfkc-lower.tsv.xz) | 609,420,802 | 2,177,257 |
| Portuguese<sub>regex</sub> | [668,519](results/ptwiki-frequency-20221020.tsv.xz) | [581,022](results/ptwiki-frequency-20221020-lower.tsv.xz) | [668,448](results/ptwiki-frequency-20221020-nfkc.tsv.xz) | [580,936](results/ptwiki-frequency-20221020-nfkc-lower.tsv.xz) | 300,393,740 | 1,852,956 |
| Russian<sub>regex</sub> | [2,069,825](results/ruwiki-frequency-20221020.tsv.xz) | [1,855,011](results/ruwiki-frequency-20221020-lower.tsv.xz) | [2,069,754](results/ruwiki-frequency-20221020-nfkc.tsv.xz) | [1,854,929](results/ruwiki-frequency-20221020-nfkc-lower.tsv.xz) | 535,069,600 | 4,483,522 |
| Spanish<sub>regex</sub> | [1,124,362](results/eswiki-frequency-20221020.tsv.xz) | [987,228](results/eswiki-frequency-20221020-lower.tsv.xz) | [1,124,249](results/eswiki-frequency-20221020-nfkc.tsv.xz) | [987,097](results/eswiki-frequency-20221020-nfkc-lower.tsv.xz) | 685,238,612 | 3,637,655 |
| Chinese<sub>jieba, <b>experimental</b></sub> | [1,422,156](results/zhwiki-frequency-20221020.tsv.xz) | [1,404,023](results/zhwiki-frequency-20221020-lower.tsv.xz) | [1,422,029](results/zhwiki-frequency-20221020-nfkc.tsv.xz) | [1,403,918](results/zhwiki-frequency-20221020-nfkc-lower.tsv.xz) | 271,265,437 | 2,456,160 |

The word lists for all the above languages are generated from dumps from 20 October 2022.

Furthermore, the project provides a script for generating the lists that can be applied to other Wikipedia languages.

## About the wordlist files

For each word, the files (linked in the table above) list:
- number of occurrences,
- number of documents (Wikipedia articles).

Words occurring in less than 3 articles are not included. The lists are sorted by the number of occurrences. The data is tab-separated with a header, and the file is compressed with LZMA2 (`xz`).

**Important:** The last row labeled `[TOTAL]` lists the **total numbers** of tokens and articles, and thus may **require special handling**. Also, note that the totals are not sums of the previous rows' values.

## How is this different from [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency)?

We strive for data that is cleaner (not containing spurious “words” such as `br` or `colspan`), and linguistically meaningful (correctly segmented, with consistent criteria for inclusion in the list). Here are the specific differences:

1. **Cleanup:** We remove HTML tags such as (`<br>`, `<ref>`, etc.), table formatting (`colspan`, `rowspan`), placeholders for formulas and code (`formula_…`, `codice_…`) or ruby (furigana).

2. **Tokenization:** We tokenize **Japanese** and **Chinese**, see [About mutations](#about-mutations). This is necessary, because these languages do not separate words with spaces. (The [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency) script, simply extracts and counts any contiguous chunks of characters, which can range from a word to a whole sentence.)

    We tokenize **other languages** using a regular expression for orthographic words, consistently treating hyphen `-` and apostrophe `'` as punctuation that cannot occur inside a word. (The wikipedia-word-frequency script allows these characters except start or end of word, thus allowing `women's` but excluding `mens'`. It also blindly converts en-dashes to hyphens, e.g. tokenizing `New York–based` as `New` and `York-based`, and right single quotation marks to apostrophes, resulting into further discrepancies.)

    For **English**, in addition to the default regex tokenization, we also provide the Penn Treebank tokenization (e.g. `can't` segmented as `ca` and `n't`). In this case, apostrophes are allowed, and we also do a smart conversion of right single quotation marks to apostrophes (to distinguish the intended apostrophe in `can’t` from the actual quotation mark in `‘tuna can’`).

3. **Inclusion criteria:** We count [words](#what-is-considered-a-word) of any length, including one-character words (such as “I” or “a” in English or “茶” in Japanese or Chinese, which aren't counted by wikipedia-word-frequency).

4. **Normalization:** For all languages, we provide [mutations](#about-mutations) that are lowercased and/or normalized to NFKC.

Additionally, the script for generating the wordlists supports **multiprocessing** (processing several dump files of the same language in parallel), greatly reducing the wall-clock time necessary to process the dumps.

## About mutations

For each language we provide several mutations.

* **All languages** have the following mutations distinguished by the filename suffixes:
    - `….tsv.xz`: no normalization,
    - `…-lower.tsv.xz`: no normalization, lowercased,
    - `…-nfkc.tsv.xz`: NFKC normalization
    - `…-nfkc-lower.tsv.xz`: NFKC normalization, lowercased

  In addition to that, there are two variants of English and Japanese tokenization:

* **English:**
    - regex tokenization (same as for Czech, French, etc.)
    - filename contains `-penn`: improved Penn Treebank tokenization from `nltk.tokenize.word_tokenize`

* **Japanese:** We do the same processing and provide the same mutations for Japanese [as in TUBELEX-JA](https://github.com/adno/tubelex#about-mutations):
    - Unidic Lite tokenization
    - filename contains `-310`: Unidic 3.1.0 tokenization

**Chinese** is tokenized using the `jieba` tokenizer. See [Further work and similar lists](#further-work-and-similar-lists) for caveats about experimental Chinese support.

## What is considered a word?

1. **English with Penn Treebank tokenization**: Tokens that fulfil the following conditions:
    - do not contain digits
    - start with a word character (\w), apostrophe, or dash.
    - end with a word character (\w), apostrophe, dash, or period.

    E.g. `a`, `o'clock`, `'coz`, `pre-/post-`, `U.S.A.`, but not `42`, `R2D2`, `...` or `.`.

2. Japanese and Chinese: Tokens that fulfil the following conditions:
    - do not contain digits (characters, such `一二三` are not considered digits),
    - start and end with a word character (\w) or wave dash (`〜`).

3. Other languages and English with the default regex tokenization:
    - tokens that consist of word characters (\w) except digits.
  
The default regex tokenization considers all non-word characters (\W, i.e. not \w) word separators. Therefore, while in English with Penn Treebank tokenization some tokens (e.g. `R2D2`) are excluded, with the regex tokenization, tokens that would have to be excluded do not occur in the first place (e.g. `R2D2` is tokenized as `R` and `D`).

# Usage

1. Install requirements:

    `pip install -r requirements.txt`
    
2. Download and process dumps (default date and languages):

    `zsh run.sh`
    
    Alternatively download and process dumps from specific date and languages:
   
    `zsh run.sh 20221020 cs sk`

For usage of the Python script for processing the dumps, see `python word_frequency.py --help`.

# Further work and similar lists

The word lists contain only the surface forms of the words (segments). For many purposes, lemmas, POS and other information would be more useful. We plan to add further processing later.

Support for Chinese is only experimental. Chinese is currently processed "as is" without any conversion, which means that it's a mix of traditional and simplified characters (and also of different varieties of Chinese used on the Chinese Wikipedia). We also do not filter vocabulary/script variants (e.g. `-{zh-cn:域;zh-tw:體}-` or `-{A|zh-hans:用户; zh-hant:使用者}-`), which has the side effect of increasing the occurrences of tokens such as `zh`, `hans`, etc. The word list may still be fine for some NLP applications.

You may also like [TUBELEX-JA](https://github.com/adno/tubelex/), a large word list based on Japanese subtitles for YouTube videos, which is processed in a similar way.
