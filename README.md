# About wikipedia-word-frequency-clean

This project provides word frequency lists generated from cleaned-up Wikipedia dumps for several languages. The following table shows the number of **words** (types) for each language and [mutation](#about-mutations) (2nd–5th column) with **links to the list files**, as well as the number of **tokens** and **articles** (6th and 7th column).

| Language / Mutation | no&nbsp;norm. | no&nbsp;norm., lowercased | NFKC&nbsp;norm. | NFKC&nbsp;norm., lowercased | #tokens | #articles |
|:------------------- | -------------:| -------------------------:| ---------------:| ---------------------------:|  -------:| ---------:|
| Czech<sub>regex</sub> | [866,635](results/cswiki-frequency-20221020.tsv.xz) | [772,788](results/cswiki-frequency-20221020-lower.tsv.xz) | [866,619](results/cswiki-frequency-20221020-nfkc.tsv.xz) | [772,771](results/cswiki-frequency-20221020-nfkc-lower.tsv.xz) | 137,564,164 | 832,967 |
| English<sub>regex</sub> | [2,419,333](results/enwiki-frequency-20221020.tsv.xz) | [2,162,061](results/enwiki-frequency-20221020-lower.tsv.xz) | [2,419,123](results/enwiki-frequency-20221020-nfkc.tsv.xz) | [2,161,820](results/enwiki-frequency-20221020-nfkc-lower.tsv.xz) | 2,489,387,103 | 16,699,990 |
| English<sub>Penn</sub> | [2,988,260](results/enwiki-frequency-20221020-penn.tsv.xz) | [2,709,385](results/enwiki-frequency-20221020-penn-lower.tsv.xz) | [2,988,187](results/enwiki-frequency-20221020-penn-nfkc.tsv.xz) | [2,709,302](results/enwiki-frequency-20221020-penn-nfkc-lower.tsv.xz) | 2,445,526,919 | 16,699,990 |
| French<sub>regex</sub> | [1,187,843](results/frwiki-frequency-20221020.tsv.xz) | [1,061,089](results/frwiki-frequency-20221020-lower.tsv.xz) | [1,187,646](results/frwiki-frequency-20221020-nfkc.tsv.xz) | [1,060,849](results/frwiki-frequency-20221020-nfkc-lower.tsv.xz) | 842,907,281 | 4,108,861 |
| German<sub>regex</sub> | [2,690,869](results/dewiki-frequency-20221020.tsv.xz) | [2,556,353](results/dewiki-frequency-20221020-lower.tsv.xz) | [2,690,793](results/dewiki-frequency-20221020-nfkc.tsv.xz) | [2,556,249](results/dewiki-frequency-20221020-nfkc-lower.tsv.xz) | 893,385,641 | 4,455,795 |
| Italian<sub>regex</sub> | [960,238](results/itwiki-frequency-20221020.tsv.xz) | [852,087](results/itwiki-frequency-20221020-lower.tsv.xz) | [960,149](results/itwiki-frequency-20221020-nfkc.tsv.xz) | [851,996](results/itwiki-frequency-20221020-nfkc-lower.tsv.xz) | 522,839,613 | 2,783,290 |
| Japanese<sub>Unidic&nbsp;Lite</sub> | [549,745](results/jawiki-frequency-20221020.tsv.xz) | [522,590](results/jawiki-frequency-20221020-lower.tsv.xz) | [549,358](results/jawiki-frequency-20221020-nfkc.tsv.xz) | [522,210](results/jawiki-frequency-20221020-nfkc-lower.tsv.xz) | 610,467,200 | 2,177,257 |
| Japanese<sub>Unidic&nbsp;3.1.0</sub> | [561,212](results/jawiki-frequency-20221020-310.tsv.xz) | [535,726](results/jawiki-frequency-20221020-310-lower.tsv.xz) | [560,821](results/jawiki-frequency-20221020-310-nfkc.tsv.xz) | [535,341](results/jawiki-frequency-20221020-310-nfkc-lower.tsv.xz) | 609,365,356 | 2,177,257 |
| Portuguese<sub>regex</sub> | [668,333](results/ptwiki-frequency-20221020.tsv.xz) | [580,948](results/ptwiki-frequency-20221020-lower.tsv.xz) | [668,262](results/ptwiki-frequency-20221020-nfkc.tsv.xz) | [580,862](results/ptwiki-frequency-20221020-nfkc-lower.tsv.xz) | 300,324,703 | 1,852,956 |
| Russian<sub>regex</sub> | [2,069,646](results/ruwiki-frequency-20221020.tsv.xz) | [1,854,875](results/ruwiki-frequency-20221020-lower.tsv.xz) | [2,069,575](results/ruwiki-frequency-20221020-nfkc.tsv.xz) | [1,854,793](results/ruwiki-frequency-20221020-nfkc-lower.tsv.xz) | 535,032,557 | 4,483,522 |
| Spanish<sub>regex</sub> | [1,124,168](results/eswiki-frequency-20221020.tsv.xz) | [987,078](results/eswiki-frequency-20221020-lower.tsv.xz) | [1,124,055](results/eswiki-frequency-20221020-nfkc.tsv.xz) | [986,947](results/eswiki-frequency-20221020-nfkc-lower.tsv.xz) | 685,158,870 | 3,637,655 |
| Chinese<sub>jieba,&nbsp;<b>experimental</b></sub> | [1,422,002](results/zhwiki-frequency-20221020.tsv.xz) | [1,403,896](results/zhwiki-frequency-20221020-lower.tsv.xz) | [1,421,875](results/zhwiki-frequency-20221020-nfkc.tsv.xz) | [1,403,791](results/zhwiki-frequency-20221020-nfkc-lower.tsv.xz) | 271,230,431 | 2,456,160 |
| Indonesian<sub>regex</sub> | [433,387](results/idwiki-frequency-20240801.tsv.xz) | [373,475](results/idwiki-frequency-20240801-lower.tsv.xz) | [433,376](results/idwiki-frequency-20240801-nfkc.tsv.xz) | [373,461](results/idwiki-frequency-20240801-nfkc-lower.tsv.xz) | 117,956,650 | 1,314,543 |

The word lists for all the above languages are generated from dumps dated 20 October 2022, with the exception of Indonesian, which is generated from a dump dated 1 August 2024.

Furthermore, the project provides a script for generating the lists that can be applied to other Wikipedia languages.

## About the wordlist files

For each word, the files (linked in the table above) list:
- number of occurrences,
- number of documents (Wikipedia articles).

Words occurring in less than 3 articles are not included. The lists are sorted by the number of occurrences. The data is tab-separated with a header, and the file is compressed with LZMA2 (`xz`).

**Important:** The last row labeled `[TOTAL]` lists the **total numbers** of tokens and articles, and thus may **require special handling**. Also, note that the totals are not sums of the previous rows' values.

## How is this different from [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency)?

We strive for data that is cleaner (not containing spurious “words” such as `br` or `colspan`), and linguistically meaningful (correctly segmented, with consistent criteria for inclusion in the list). Here are the specific differences:

1. **Cleanup:** We remove HTML/Wikitext tags such as (`<br>`, `<ref>`, etc.), table formatting (e.g. `colspan`, `rowspan`), some non-textual content (such as musical scores), placeholders for formulas and code (`formula_…`, `codice_…`) or ruby (furigana).

2. **Tokenization:** We tokenize **Japanese** and **Chinese**, see [About mutations](#about-mutations). This is necessary because these languages do not separate words with spaces. (The [wikipedia-word-frequency](https://github.com/IlyaSemenov/wikipedia-word-frequency) script simply extracts and counts any contiguous chunks of characters, which can range from a word to a whole sentence.)

    We tokenize **other languages** using a regular expression for orthographic words, consistently treating hyphen `-` and apostrophe `'` as punctuation that cannot occur inside a word. (The wikipedia-word-frequency script allows these characters except start or end of word, thus allowing `women's` but excluding `mens'`. It also blindly converts en-dashes to hyphens, e.g. tokenizing `New York–based` as `New` and `York-based`, and right single quotation marks to apostrophes, resulting into further discrepancies.)

    For **English**, in addition to the default regex tokenization, we also provide the Penn Treebank tokenization (e.g. `can't` segmented as `ca` and `n't`). In this case, apostrophes are allowed, and we also do a smart conversion of right single quotation marks to apostrophes (to distinguish the intended apostrophe in `can’t` from the actual quotation mark in `‘tuna can’`).

3. **Normalization:** For all languages, we provide [mutations](#about-mutations) that are lowercased and/or normalized to NFKC.

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
    - contains at least one word character (\w).

    E.g. `a`, `o'clock`, `'coz`, `pre-/post-`, `U.S.A.`, `LGBTQ+`, but not `42`, `R2D2`, `...` or `.`.

2. Japanese and Chinese: Tokens that fulfil the following conditions:
    - do not contain digits (characters, such `一二三` are not considered digits),
    - start and end with a word character (\w), or wave dash (`〜`) in case of Japanese (e.g. `あ〜`).

3. Other languages and English with the default regex tokenization:
    - tokens that consist of word characters (\w) except digits.
  
The default regex tokenization considers all non-word characters (\W, i.e. not \w) word separators. Therefore, while in English with Penn Treebank tokenization some tokens (e.g. `R2D2`) are excluded, with the regex tokenization, tokens that would have to be excluded do not occur in the first place (e.g. `R2D2` is tokenized as `R` and `D`).

# Usage

1. Install requirements:

    `pip install -r requirements.txt`
    
2. Download and process dumps (default date and languages):

    `zsh run.sh`
    
    Alternatively, download and process dumps from specific date and languages:
   
    `zsh run.sh 20221020 cs sk`

The `run.sh` script also outputs the table in this readme.

For usage of the Python script for processing the dumps, see `python word_frequency.py --help`.

# Further work and similar lists

The word lists contain only the surface forms of the words (segments). For many purposes, lemmas, POS, and other information would be more useful. We plan to add further processing later.

Support for Chinese is only experimental. Chinese is currently processed “as is” without any conversion, which means that it's a mix of traditional and simplified characters (and also of different varieties of Chinese used on the Chinese Wikipedia). We also do not filter vocabulary/script variants (e.g. `-{zh-cn:域;zh-tw:體}-` or `-{A|zh-hans:用户; zh-hant:使用者}-`), which has the side effect of increasing the occurrences of tokens such as `zh`, `hans`, etc. The word list may still be fine for some NLP applications.

We are using [wikiextractor](https://github.com/attardi/wikiextractor) to extract plain text from Wikipedia dumps. Ideally, almost no cleanup would be necessary after using this tool, but there is actually a substantial amount of non-textual content such as maps, musical scores, tables, math formulas and random formatting that wikiextractor doesn't remove or removes in a haphazard fashion (see the [issue on GitHub](https://github.com/attardi/wikiextractor/issues/300)). We try to remove both the legit placeholders and markup and also the most common markup that ought to be filtered by wikiextractor but isn't. The results are still imperfect, but rather than extending the removal in this tool, it would be better to fix wikiextractor. Another option would be to use the Wikipedia Cirrus search dumps instead (see [this issue and my comment](https://github.com/attardi/wikiextractor/issues/282)). Note that both approaches have been used to get pretraining data for large language models.

In the current version we have added Indonesian from a later dump. We observed the string "https" among relatively high frequency words, which means that our cleanup is less effective for the current Wikipedia dumps.

You may also like [TUBELEX-JA](https://github.com/adno/tubelex/), a large word list based on Japanese subtitles for YouTube videos, which is processed in a similar way.
