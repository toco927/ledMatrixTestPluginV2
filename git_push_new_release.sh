#!/bin/bash
set -e

FILE="manifest.json"

# get current version
current=$(jq -r '.version' "$FILE")

# split
IFS='.' read -r major minor patch <<< "$current"

# bump patch
patch=$((patch + 1))
new_version="$major.$minor.$patch"

echo "Bumping: $current → $new_version"

# update JSON
jq --arg v "$new_version" '
  .version=$v |
  .versions[-1].version=$v |
  .versions[-1].released=(now | strftime("%Y-%m-%d"))
' "$FILE" > tmp.json && mv tmp.json "$FILE"

# git
git add -A
git commit -m "Update script for version $new_version"
git tag v$new_version
git push origin main
git push origin v$new_version

echo "Done: v$new_version"