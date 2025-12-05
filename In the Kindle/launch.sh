#! /bin/sh
PATH=/usr/bin:/bin:/usr/sbin:/sbin
export PATH

while [ ! -d /mnt/us ]; do
    sleep 1
done

LOG_FILE="/mnt/us/linkss/screensavers/launch.log"

# Truncate log file
echo "--- Starting launch.sh at $(date) ---" > $LOG_FILE

# Download new wallpapers to temporary files
echo "Downloading done_0.png..." >> $LOG_FILE
wget -O "/mnt/us/linkss/screensavers/done_0.png.new" "http://192.168.174.153/done_0.png" >> $LOG_FILE 2>&1
echo "wget exit code for done_0.png: $?" >> $LOG_FILE

echo "Downloading done_1.png..." >> $LOG_FILE
wget -O "/mnt/us/linkss/screensavers/done_1.png.new" "http://192.168.174.153/done_1.png" >> $LOG_FILE 2>&1
echo "wget exit code for done_1.png: $?" >> $LOG_FILE

REPLACED_ANY=0

# Process done_0.png
echo "Processing done_0.png..." >> $LOG_FILE
if [ -s "/mnt/us/linkss/screensavers/done_0.png.new" ]; then
    echo "done_0.png.new is not empty." >> $LOG_FILE
    if [ ! -f "/mnt/us/linkss/screensavers/done_0.png" ] || \
       [ "$(md5sum /mnt/us/linkss/screensavers/done_0.png.new | awk '{print $1}')" != "$(md5sum /mnt/us/linkss/screensavers/done_0.png | awk '{print $1}')" ]; then
        echo "Replacing done_0.png." >> $LOG_FILE
        mv "/mnt/us/linkss/screensavers/done_0.png.new" "/mnt/us/linkss/screensavers/done_0.png"
        REPLACED_ANY=1
    else
        echo "done_0.png is already up to date." >> $LOG_FILE
    fi
else
    echo "done_0.png.new is empty or does not exist." >> $LOG_FILE
fi

# Process done_1.png
echo "Processing done_1.png..." >> $LOG_FILE
if [ -s "/mnt/us/linkss/screensavers/done_1.png.new" ]; then
    echo "done_1.png.new is not empty." >> $LOG_FILE
    if [ ! -f "/mnt/us/linkss/screensavers/done_1.png" ] || \
       [ "$(md5sum /mnt/us/linkss/screensavers/done_1.png.new | awk '{print $1}')" != "$(md5sum /mnt/us/linkss/screensavers/done_1.png | awk '{print $1}')" ]; then
        echo "Replacing done_1.png." >> $LOG_FILE
        #mv "/mnt/us/linkss/screensavers/done_1.png.new" "/mnt/us/linkss/screensavers/done_1.png"
        rm -f "/mnt/us/linkss/screensavers/done_1.png.new"
        rm -f "/mnt/us/linkss/screensavers/done_1.png"
        REPLACED_ANY=1
    else
        echo "done_1.png is already up to date." >> $LOG_FILE
    fi
else
    echo "done_1.png.new is empty or does not exist." >> $LOG_FILE
fi

# Clean up any leftover .new files
echo "Cleaning up .new files..." >> $LOG_FILE
rm -f "/mnt/us/linkss/screensavers/done_0.png.new"
rm -f "/mnt/us/linkss/screensavers/done_1.png.new"

# Reboot only if a file was actually replaced
if [ $REPLACED_ANY -eq 1 ]; then
    echo "A file was replaced. Rebooting would happen here." >> $LOG_FILE
    #reboot
else
    echo "No files were replaced." >> $LOG_FILE
fi

echo "--- Finished launch.sh at $(date) ---" >> $LOG_FILE