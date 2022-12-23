# Usage: zsh run.sh [DATE [LANGUAGES]]
#
# Automate download and word frequency list generation.
#
# See `wordfrequency.py --help` for options of the tool used in the script.
#
# Based on https://github.com/notani/wikipedia-word-frequency/blob/master/run.sh by Naoki Otani

# We generate several variants for JA and EN:

JA_OPTS="--ja/--ja -D unidic"
JA_SUFFIXES="/-310"

EN_OPTS="--auto/--en/--en -relaxed"
EN_SUFFIXES="/-penn/-pennr"


DATE=$1
if [ -z "$DATE" ]
then
	DATE="20221020"
fi

if [ "$#" -ge 1 ]
then
	shift 1
fi

LANGS="$@"
if [ -z "$LANGS" ]
then
	LANGS="de en es fr it ru zh pt ja cs"
fi

for lang in ${=LANGS}
do
    if [ -e results/${lang}wiki-frequency-${DATE}.tsv ]; then
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
    	suffixes=""
    elif [ $lang = "ja" ]
    then
    	opts="$JA_OPTS"
    	suffixes="$JA_SUFFIXES"
    else
    	# Explicit --default ensures we do an iteration.
    	opts="--default"
    	suffixes=""
    fi
    
    for opt in "${(@s:/:)opts}"
    do
    	suffix="${suffixes%%/*}"
    	suffixes="${suffixes#*/}"
    	
		cmd="python word_frequency.py -x $opt dumps.wikimedia.org/${lang}wiki/${DATE}/*.bz2 -o results/${lang}wiki-frequency-${DATE}%.tsv"
		echo $cmd
		eval $cmd
    done
    
done
