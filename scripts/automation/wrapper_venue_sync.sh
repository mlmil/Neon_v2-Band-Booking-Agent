#!/bin/bash
set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
LOCKDIR="/tmp/neon_venue_sync.lock"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "$(date) [INFO] Already running. Exiting." >&2
    exit 0
fi
trap "rm -rf '$LOCKDIR'" EXIT

cd "$REPO_DIR"

if [ -f ".secrets/neon-v2.env" ]; then
    set -a
    source ".secrets/neon-v2.env"
    set +a
fi

echo "$(date) [INFO] Starting venue folder sync"
python3 scripts/local_venue_folder_sync.py --sync-calendar --use-local-model
echo "$(date) [INFO] Finished venue folder sync"

echo "$(date) [INFO] Starting payout CSV sync"
python3 scripts/payout_csv_sync.py
echo "$(date) [INFO] Finished payout CSV sync"
