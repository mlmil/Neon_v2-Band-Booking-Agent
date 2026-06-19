#!/bin/bash
set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
LOCKDIR="/tmp/neon_groupme_sync.lock"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "$(date) [INFO] Already running. Exiting." >&2
    exit 0
fi
trap "rm -rf '$LOCKDIR'" EXIT

if [ ! -d "$REPO_DIR" ]; then
    echo "$(date) [ERROR] Neon V2 repository is unavailable. Halting sync." >&2
    exit 1
fi

cd "$REPO_DIR"

if [ -f ".secrets/neon-v2.env" ]; then
    set -a
    source ".secrets/neon-v2.env"
    set +a
fi

echo "$(date) [INFO] Fetching GroupMe messages"
python3 scripts/fetch_groupme_messages.py

echo "$(date) [INFO] Syncing GroupMe messages"
python3 scripts/sync_groupme_messages.py

echo "$(date) [INFO] Finished GroupMe sync"
