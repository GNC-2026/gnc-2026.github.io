#!/bin/bash
# usage: tools/update.sh <live.json>   — rebuild index.html from the dashboard's live data; commit + push only if it changed
cd "$(dirname "$0")/.." || exit 1
python3 tools/build.py "$1" . >/dev/null || { echo "build failed"; exit 1; }
if git diff --quiet -- index.html; then echo "no change"; exit 0; fi
git add index.html && git -c user.name="GNC BPL scoreboard" -c user.email="noreply@anthropic.com" commit -qm "Update results" && git -c push.negotiate=true push -q 2>&1 | tail -1
echo "pushed $(grep -o 'Results as of [^·]*' index.html)"
