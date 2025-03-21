#!/bin/bash

# Define the base directory
BASE_DIR="/Volumes/JC Data HD 8-26-2022"

# Check if the directory exists
if [ ! -d "$BASE_DIR" ]; then
    echo "Directory '$BASE_DIR' not found. Ensure the drive is mounted."
    exit 1
fi

# Use find to locate .mp4 and .MP4 files and get their last modified dates
echo "Searching for .mp4 and .MP4 files in '$BASE_DIR'..."
find "$BASE_DIR" -type f \( -iname "*.mp4" \) -print0 | while IFS= read -r -d '' file; do
    # Get the last modified date using stat (macOS format)
    mod_date=$(stat -f "%Sm" "$file")
    echo "File: $file | Last Modified: $mod_date"
done

# Check if any files were found (count them after the fact)
file_count=$(find "$BASE_DIR" -type f \( -iname "*.mp4" \) | wc -l)
if [ "$file_count" -eq 0 ]; then
    echo "No .mp4 or .MP4 files found."
else
    echo "Found $file_count .mp4/.MP4 files."
fi