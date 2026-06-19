#!/usr/bin/env bash
set -euo pipefail

REPO="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2"
ENV_FILE="$REPO/.secrets/neon-v2.env"

cd "$REPO"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

/opt/homebrew/bin/python3 scripts/post_gig_reminder.py
