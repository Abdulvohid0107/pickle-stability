#!/usr/bin/env bash
# One-time script to push this repo to your own GitHub account.
#
# PREREQUISITES:
#   1. Create an EMPTY repo on github.com (no README/license) named e.g. pickle-stability
#   2. Have git installed and be logged in (gh auth login, or have a PAT ready)
#
# USAGE:
#   bash PUSH_TO_GITHUB.sh https://github.com/YOUR_USERNAME/pickle-stability.git

set -e
REMOTE="$1"
if [ -z "$REMOTE" ]; then
  echo "Usage: bash PUSH_TO_GITHUB.sh https://github.com/YOUR_USERNAME/pickle-stability.git"
  exit 1
fi

git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"
git branch -M main
git push -u origin main

echo ""
echo "Done. Now update the repository link in:"
echo "  - README.md"
echo "  - docs/Final_Report.docx (Section 7)"
echo "replacing USERNAME with your GitHub username."
