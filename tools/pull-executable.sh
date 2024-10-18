#!/bin/bash

# Directory to copy the executable
TAG=$(<./internal/executable/release-tag.txt)

# Function to pull a specific release
pull_release() {
    echo "Pulling release tag: $1"
    wget https://github.com/mgastner/cartogram-cpp/releases/download/$1/cartogram -P ./internal/executable

    # Overwrite version.txt with the release tag
    echo $1 > ./internal/executable/release-tag.txt
}

# Function to pull the latest release
pull_latest() {
    echo "Pulling latest release"
    LATEST_TAG=$(curl -s https://api.github.com/repos/mgastner/cartogram-cpp/releases/latest | grep 'tag_name' | cut -d\" -f4)
    pull_release $LATEST_TAG
}

# Check for --latest option
if [ "$1" == "--latest" ]; then
    pull_latest
else
    pull_release $TAG
fi