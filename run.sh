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

EN_OPTS="--default/--en"
EN_SUFFIXES="/-penn"

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
	LANGS="cs en fr de it ja pt ru es zh"
fi

for lang in ${=LANGS}
do
    if [ -e results/${lang}wiki-frequency-${DATE}.tsv.xz ]; then
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
    elif [ $lang = "en" ]
    then
    	opts="$EN_OPTS"
    	suffixes="$EN_SUFFIXES"
    else
    	# Explicit --default ensures we do an iteration.
    	opts="--default"
    	suffixes=""
    fi
    
    for opt in "${(@s:/:)opts}"
    do
    	suffix="${suffixes%%/*}"
    	suffixes="${suffixes#*/}"
    	
		cmd="python word_frequency.py -x $opt dumps.wikimedia.org/${lang}wiki/${DATE}/*.bz2 -o results/${lang}wiki-frequency-${DATE}${suffix}%.tsv.xz"
		echo $cmd
		eval $cmd
    done
    
done

typeset -A LANGNAMES MUTNAMES SUFNAMES
LANGNAMES=(
	[cs]=Czech
	[en]=English
	[fr]=French
	[de]=German
	[it]=Italian
	[ja]=Japanese
	[pt]=Portuguese
	[ru]=Russian
	[es]=Spanish
	[zh]=Chinese
	)
SUFNAMES=(
	[]="regex"
	[zh]="jieba,&nbsp;<b>experimental</b>"
	[ja]="Unidic&nbsp;Lite"
	[-310]="Unidic&nbsp;3.1.0"
	[-penn]="Penn"
)
MUTATIONS="/-lower/-nfkc/-nfkc-lower"
MUTNAMES=(
	[]="no&nbsp;norm."
	[-lower]="no&nbsp;norm., lowercased"
	[-nfkc]="NFKC&nbsp;norm."
	[-nfkc-lower]="NFKC&nbsp;norm., lowercased"
	)
	
table_fmt='|:------------------- |'
echo -n   '| Language / Mutation |'
for mutation in "${(@s:/:)MUTATIONS}"
do
	mutname="$MUTNAMES[$mutation]"
	dashes="$(echo $mutname | sed 's/./-/g')"
	echo -n   " ${mutname} |"
	table_fmt="${table_fmt} ${dashes}:|"
done
echo            " #tokens | #articles |"
echo "$table_fmt  -------:| ---------:|"


for lang in ${=LANGS}
do
	if [ $lang = "ja" ]
    then
    	suffixes="$JA_SUFFIXES"
    elif [ $lang = "en" ]
    then
    	suffixes="$EN_SUFFIXES"
    else
    	suffixes=""
    fi
    langname="$LANGNAMES[$lang]"
    	
    for suffix in "${(@s:/:)suffixes}"
    do
    	if [ -z "$suffix" ] && [ $lang = "ja" -o $lang = "zh" ]
    	then
	    	sufname="$SUFNAMES[$lang]"
	    else
    		sufname="$SUFNAMES[$suffix]"
    	fi
    	echo -n "| ${langname}<sub>${sufname}</sub> |"
    	for mutation in "${(@s:/:)MUTATIONS}"
    	do
		    mutname="$MUTNAMES[$mutation]"
			file="results/${lang}wiki-frequency-${DATE}${suffix}${mutation}.tsv.xz"
			totals=$(xzcat $file | awk 'END{ print NR-2, $2, $3 }')
			types="${totals%% *}"
			tokens_docs="${totals#* }"
			tokens="${tokens_docs% *}"
			docs="${tokens_docs#* }"
			printf " [%'d]($file) |" "$types"
		done
		printf " %'d | %'d |\n" "$tokens" "$docs"
    done
done
