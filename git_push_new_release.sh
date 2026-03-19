#!/bin/bash

v=$1
if [ -z "$v" ]; then
  echo "Usage: ./release.sh x.y.z"
  exit 1
fi

jq --arg v "$v" '
  .version=$v |
  .versions[-1].version=$v |
  .versions[-1].released=(now | strftime("%Y-%m-%d"))
' manifest.json > tmp.json && mv tmp.json manifest.json

git add -A &&
git commit -m "Update script for version $v" &&
git tag v$v &&
git push origin main &&
git push origin v$v