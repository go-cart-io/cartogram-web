#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Directory to copy the executable
TAG=$(<../internal/executable/release-tag.txt)

# Define the ANSI color code for red and escape code to reset color
RED='\033[31m'
RESET='\033[0m'

# Function to pull a specific release
pull_release() {
    printf "\nPulling release tag: ${RED}$1${RESET}\n\n"
    wget https://github.com/mgastner/cartogram-cpp/releases/download/$1/cartogram -O ../internal/executable/cartogram

    # Make the binary executable
    chmod +x ../internal/executable/cartogram
}

# Function to pull the latest release
pull_latest() {

    # Find out what the latest release tag is
    printf "\nPulling LATEST release"
    LATEST_TAG=$(curl -s https://api.github.com/repos/mgastner/cartogram-cpp/releases/latest | grep 'tag_name' | cut -d\" -f4)

    pull_release $LATEST_TAG

    # Overwrite version.txt with the release tag
    echo $1 > ../internal/executable/release-tag.txt
}

# Check for --latest option
if [ "$1" == "--latest" ]; then
    pull_latest
else
    pull_release $TAG
fi