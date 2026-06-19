#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ ! -d "${ROOT_DIR}" ]]; then
  echo "Neon V2 repository is unavailable. Mount VADER and try again." >&2
  exit 1
fi

"${ROOT_DIR}/scripts/fetch_groupme_messages.py"
"${ROOT_DIR}/scripts/sync_groupme_messages.py"
echo "GroupMe fetch and local export sync complete."
