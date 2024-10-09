#!/bin/bash

# Download the latest cartogram binary release
wget -O /root/internal/cartogram_package/cartogram https://github.com/Wind1337/cartogram-cpp/releases/latest/download/cartogram

# Give it execute permissions
chmod +x /root/internal/cartogram_package/cartogram
chmod +x /root/internal/cartogram_package/cartogram_c

# Execute the passed command
exec "$@"
