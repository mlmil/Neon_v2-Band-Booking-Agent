#!/bin/bash
set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
LOCKDIR="/tmp/neon_health_check.lock"

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

echo "$(date) [INFO] Running health check"
mkdir -p data/health
OUTPUT_FILE="data/health/receipt_$(date +%s).json"
set +e
python3 scripts/neon_health_check.py > "$OUTPUT_FILE"
STATUS=$?
set -e
echo "$(date) [INFO] Finished health check with exit code $STATUS, saved to $OUTPUT_FILE"
exit "$STATUS"
