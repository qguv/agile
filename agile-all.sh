#!/usr/bin/env zsh

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: agile-all.sh <source dir> <csv file> <log file>"
    return 1
fi

LOGFILE="$3"
echo "agile-all.sh log" > "$LOGFILE"
echo -n

DIRS=($1/*)
LENDIRS=${#DIRS[@]} # length
DIRNUM=0
for d in $DIRS; do
    echo "$d:" >> "$LOGFILE"

    LAYOUT_COUNT=0
    LAYOUTS_DIR="nothing for now"

    ALL_LAYOUT_DIRS="$(find "$d" -path '*/res/layout' | sort -r)"

    # as long as there aren't any layouts and there's still a directory to try
    while [ $LAYOUT_COUNT -lt 1 ] && [ -n "$LAYOUTS_DIR" ]; do
        LAYOUTS_DIR="$(echo $ALL_LAYOUT_DIRS | head -1)"
        LAYOUT_COUNT="$(ls $LAYOUTS_DIR | wc -l)"
        ALL_LAYOUT_DIRS="$(echo $ALL_LAYOUT_DIRS | tail -n +2)"
    done
    if [ -n "$LAYOUTS_DIR" ]; then
        echo "\trunning agile on $LAYOUTS_DIR" >> "$LOGFILE"
        python3 agile.py tags -o "$2" "$LAYOUTS_DIR" >> "$LOGFILE" 2&>1
    else
        echo "\tnothing found for $d" >> "$LOGFILE"
    fi

    let "DIRNUM += 1"
    let "PCT = DIRNUM * 100 / LENDIRS"
    printf " %2d%% - %3d of %3d complete" "$PCT" "$DIRNUM" "$LENDIRS"

    # return cursor to beginning of last line
    echo -en "\e[0K\r"

done

PROBLEMS="$(cat $LOGFILE | grep Error | wc -l)"

echo "agile-all.sh finished with $PROBLEMS problems. See $LOGFILE for more info."
