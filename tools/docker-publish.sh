#!/usr/bin/env bash
# Triggers the "Build, Publish, Release" workflow on the main branch
# with the update-server option enabled (deploys to go-cart.io).
#
# Requires: gh cli (https://cli.github.com), authenticated via `gh auth login`
#
# Usage: bash tools/docker-publish.sh

set -euo pipefail

gh workflow run docker-publish.yml \
  --ref main \
  -f update-server=true

echo "Workflow triggered. Monitor at:"
echo "  https://github.com/go-cart-io/cartogram-web/actions/workflows/docker-publish.yml"
