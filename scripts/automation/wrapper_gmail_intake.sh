#!/bin/bash
set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
LOCKDIR="/tmp/neon_gmail_intake.lock"

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

echo "$(date) [INFO] Starting Gmail intake"
python3 scripts/monitor_inbox.py --write-intake-receipts --notify-telegram
echo "$(date) [INFO] Finished Gmail intake"
