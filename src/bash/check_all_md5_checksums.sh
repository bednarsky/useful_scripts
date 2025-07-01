#!/bin/bash

# Script to check all md5 checksums in a given directory.

# --- Configuration ---
# Set to 1 to suppress the "OK" messages and only show errors/warnings.
QUIET=0
# Set colors for output
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_NC='\033[0m' # No Color

# --- Functions ---
print_usage() {
    echo "Usage: $0 <directory>"
    echo "  Iterates over all *.md5 files in <directory>, and verifies the checksum"
    echo "  against the corresponding file."
}

# --- Main Script ---

# Check for correct number of arguments
if [ "$#" -ne 1 ]; then
    print_usage
    exit 1
fi

TARGET_DIR="$1"

# Check if the provided path is a directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${COLOR_RED}Error: Directory '${TARGET_DIR}' not found.${COLOR_NC}"
    exit 1
fi

echo "Scanning directory: ${TARGET_DIR}"
echo "---"

# Keep track of how many files were processed
found_md5_files=0

# Use find to handle subdirectories and filenames with spaces gracefully
# -maxdepth 1 prevents find from going into subdirectories
find "$TARGET_DIR" -maxdepth 1 -type f -name "*.md5" | while read -r md5_file; do
    ((found_md5_files++))
    
    # Derive the data file name by removing the .md5 extension
    data_file="${md5_file%.md5}"
    
    # Get just the basename for cleaner output messages
    data_filename=$(basename "$data_file")

    if [ ! -f "$data_file" ]; then
        echo -e "[${COLOR_YELLOW}SKIPPED${COLOR_NC}] Could not find corresponding file for '${data_filename}.md5'"
        continue
    fi

    # Read the expected checksum from the .md5 file. It should be the first word.
    expected_checksum=$(awk '{print $1}' "$md5_file")
    
    # Calculate the actual checksum of the data file.
    # We need to be in the file's directory so that the path in the checksum file (if any) matches.
    actual_checksum=$(cd "$(dirname "$data_file")" && md5sum "$(basename "$data_file")" | awk '{print $1}')

    if [ "$expected_checksum" == "$actual_checksum" ]; then
        # Checksum is correct
        if [ "$QUIET" -eq 0 ]; then
            echo -e "[${COLOR_GREEN}OK${COLOR_NC}]      Checksum for '${data_filename}' is correct."
        fi
    else
        # Checksum is incorrect
        echo -e "[${COLOR_RED}FAILED${COLOR_NC}]  Checksum for '${data_filename}' does NOT match."
    fi
done

if [ "$found_md5_files" -eq 0 ]; then
    echo -e "${COLOR_YELLOW}No .md5 files found in '${TARGET_DIR}'.${COLOR_NC}"
fi

echo "---"
echo "Done."