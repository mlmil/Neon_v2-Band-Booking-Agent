#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -d "/Volumes/Drive_A/GroupMeChats/messages" ]]; then
  echo "Drive_A is not mounted. Mount the Drive A shared drive and try again." >&2
  exit 1
fi

"${ROOT_DIR}/scripts/sync_groupme_messages.py"
echo "GroupMe sync complete. Continue with Neon Blonde booking workflows."
