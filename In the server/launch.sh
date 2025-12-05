#!/bin/sh

LOCKFILE="/tmp/kindle-wallpaper.lock"

if [ -e "$LOCKFILE" ]; then
    echo "Lockfile exists, another instance is running."
    exit 1
fi

trap 'rm -f "$LOCKFILE"' EXIT
touch "$LOCKFILE"

cd "$(dirname "$0")"

# Unset PYTHONPATH to prevent conflicts with the virtual environment
unset PYTHONPATH

# Run python from the virtual environment directly
.venv/bin/python3 programs/parse_ical.py

# Define the pages to process in a loop
for page_num in 0 1; do
    svg_file="almost_done_${page_num}.svg"
    
    if [ -e "$svg_file" ]; then
        png_file="almost_done_${page_num}.png"
        done_file="done_${page_num}.png"

        echo "Processing $svg_file..."

        rsvg-convert --background-color=white -o "$png_file" "$svg_file"
        pngcrush -force -c 0 "$png_file" "$done_file"

        if [ -d "/var/www/kindle/" ]; then
            echo "$(date): Moving $done_file to /var/www/kindle/"
            #rm -f "/var/www/kindle/$done_file"
            mv -f "$done_file" "/var/www/kindle/"
        fi

        # Cleanup intermediate files
        rm "$png_file"
        rm "$svg_file"
    fi
done

rm -f basic.ics

