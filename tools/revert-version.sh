#!/usr/bin/env bash
# Reverts go-cart.io to a specific previously released version.
#
# Requires: gh cli (https://cli.github.com), authenticated via `gh auth login`
#
# Usage: bash tools/revert-version.sh <version>
# Example: bash tools/revert-version.sh 4.4.0

set -euo pipefail

VERSION="${1:?Usage: bash tools/revert-version.sh <version>}"

gh workflow run revert-version.yml \
  --ref main \
  -f version="$VERSION"

echo "Reverting go-cart.io to version $VERSION."
echo "Monitor at:"
echo "  https://github.com/go-cart-io/cartogram-web/actions/workflows/revert-version.yml"
