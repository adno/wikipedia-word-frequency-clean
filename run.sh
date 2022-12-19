# Usage: zsh run.sh [DATE [LANG1 [...]]]
# Default date: 20221020 
# Default language list: de en es fr it ru zh pt ja cs

# The scripts does segmentation of Japanese using both IPADIC and UNIDIC.
# If you want to process Japanese, install both and edit the following paths to
# match your installation. Alternatively, supply a list of languages without Japanese.

UNIDIC_DIR="~/.linuxbrew/lib/mecab/dic/unidic"
IPADIC_DIR="~/.linuxbrew/lib/mecab/dic/ipadic"


if [ "$#" -gt 0 ]
then
	DATE=$1
	shift 1
else
	DATE=20221020
fi

LANGS="$@"
if [ -z "$LANGS" ]
then
	LANGS="de en es fr it ru zh pt ja cs"
fi

for lang in ${=LANGS}
do
    if [ -e results/${lang}wiki-${DATE}-word-doc-frequency.tsv ] || [ -e results/${lang}wiki-${DATE}-unidic-word-doc-frequency.tsv ]; then
        continue
    fi

    # 1. Download
    if [ ! -d dumps.wikimedia.org/${lang}wiki/${DATE}/ ]; then
        cmd="wget -np -r --accept-regex 'https://dumps.wikimedia.org/${lang}wiki/${DATE}/${lang}wiki-${DATE}-pages-articles[0-9].*' https://dumps.wikimedia.org/${lang}wiki/${DATE}/"
        echo $cmd
        eval $cmd
		if ! (ls dumps.wikimedia.org/${lang}wiki/${DATE} | grep -q 'pages-articles')
		then
        	cmd="wget -np -r --accept-regex 'https://dumps.wikimedia.org/${lang}wiki/${DATE}/${lang}wiki-${DATE}-pages-articles\.xml\.bz2' https://dumps.wikimedia.org/${lang}wiki/${DATE}/"
			echo $cmd
			eval $cmd
		fi 
    fi

    # 2. Count
    if [ $lang = "zh" ]
    then
    	opts="--zh"
    	suffixes="-jieba"
    elif [ $lang = "ja" ]
    then
    	opts="--ja=$UNIDIC_DIR --ja=$IPADIC_DIR"
    	suffixes="-unidic -ipadic"
    else
    	# Explicit --auto ensures we do an iteration.
    	opts="--auto"
    	suffixes=""
    fi
    
    for opt in ${=opts}
    do
    	suffix="${suffixes%% *}"
    	suffixes="${suffixes#* }"
    	
		cmd="python ./gather_wordfreq.py -Dt $opt dumps.wikimedia.org/${lang}wiki/${DATE}/*.bz2 > results/${lang}wiki-${DATE}${suffix}-word-doc-frequency.tsv"
		echo $cmd
		eval $cmd
    done
    
done
