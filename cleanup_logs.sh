#!/bin/bash

# Your specific logs folder
LOG_DIR="/home/aarif/Documents/Docker_logs"

# Ensure the directory exists before trying to delete files
if [ -d "$LOG_DIR" ]; then
    # Find all .gz files older than 365 days and delete them
#    find "$LOG_DIR" -type f -name "*.gz" -mtime +365 -delete
     find "$LOG_DIR" -type f -name "*.gz" -mmin +10 -delete

    # Log the cleanup action so you have a record
    echo "Cleaned up logs older than 1 year on $(date)" >> "$LOG_DIR/cleanup.log"
else
    echo "Directory $LOG_DIR does not exist."
fi
