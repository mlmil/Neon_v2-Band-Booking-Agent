#!/bin/zsh

set -e

REPO_DIR="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
URL="http://127.0.0.1:8787/"

cd "$REPO_DIR"

if lsof -nP -iTCP:8787 -sTCP:LISTEN >/dev/null 2>&1; then
  open "$URL"
  echo "Neon V2 Dashboard is already running."
  exit 0
fi

echo "Starting Neon V2 Dashboard..."
open "$URL"
exec python3 scripts/dashboard_server.py
