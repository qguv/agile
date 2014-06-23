#!/usr/bin/env zsh

for d in fdroid/*; do
    echo "$d:"

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
        echo "\trunning agilex on $LAYOUTS_DIR"
        python3 ~/dev/agilex/agilex.py -c ~/out.csv "$LAYOUTS_DIR"
    else
        echo "\tnothing found for $d"
    fi
done
