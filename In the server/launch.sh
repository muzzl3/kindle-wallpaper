#!/bin/sh

cd "$(dirname "$0")"

# Unset PYTHONPATH to prevent conflicts with the virtual environment
unset PYTHONPATH

# Run python from the virtual environment directly
.venv/bin/python3 programs/parse_ical.py

rsvg-convert --background-color=white -o almost_done.png almost_done.svg

#We optimize the image
pngcrush -force -c 0 almost_done.png done.png

if [ -d "/var/www/kindle/" ]; then
    echo "Folder exists."
    #We move the image where it needs to be
    rm /var/www/kindle/done.png
    mv done.png /var/www/kindle/done.png
else
    echo "Folder does not exist."
fi

rm basic.ics

if [ -e "almost_done.png" ]; then
    rm almost_done.png
fi
if [ -e "almost_done.svg" ]; then
    rm almost_done.svg
fi

