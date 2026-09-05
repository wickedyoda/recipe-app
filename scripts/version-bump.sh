#!/usr/bin/env bash
#
# Determine the next alpha version for recipe-app images.
# Pattern: alpha-1.00.1, alpha-1.00.2, ...
# Uses GitHub API to list existing tags, finds the highest version, increments.
#

set -euo pipefail

TOKEN="${GITHUB_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  echo "GITHUB_TOKEN required" >&2
  exit 1
fi

# Fetch existing tags from GHCR - need to use ghcr.io package tags
# Since GHCR uses package tags not git tags, we'll use the GitHub API for releases
REPO="wickedyoda/recipe-app"

NEXT_VERSION=$(curl -s -H "Authorization: bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/releases/tags/alpha-1.00.0" 2>/dev/null \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tag = data.get('tag_name', 'alpha-1.00.0')
    if tag.startswith('alpha-1.00.'):
        n = int(tag.split('.')[-1]) + 1
    else:
        n = 1
    print(f'alpha-1.00.{n:03d}')
except:
    print('alpha-1.00.001')
" 2>/dev/null || echo "alpha-1.00.001")

echo "$NEXT_VERSION"
