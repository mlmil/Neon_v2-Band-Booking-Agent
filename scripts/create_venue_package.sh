#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <venue-name> <YYYY-MM-DD> <time-text> [alt]" >&2
  exit 1
fi

VENUE_NAME="$1"
VENUE_DATE="$2"
TIME_TEXT="$3"
USE_ALT="${4:-}"

safe_name() {
  printf '%s' "$1" | tr '/:' '__' | tr -s ' '
}

BASE_DIR="/Users/studio_hub/Library/CloudStorage/GoogleDrive-neonblondevc@gmail.com/My Drive/Venues"
VENUE_SAFE="$(safe_name "${VENUE_NAME}")"
FOLDER_NAME="${VENUE_SAFE} - ${VENUE_DATE}"
TARGET_DIR="${BASE_DIR}/${FOLDER_NAME}"
PROJECT_PATH="${TARGET_DIR}/${FOLDER_NAME}.gimp-cli.json"
NOTES_PATH="${TARGET_DIR}/notes"
ASSETS_DIR="${TARGET_DIR}/assets"

if ! command -v cli-anything-gimp >/dev/null 2>&1; then
  echo "cli-anything-gimp is not installed or not on PATH." >&2
  echo "Install the CLI-Anything GIMP harness before running this script." >&2
  exit 1
fi

if [[ -z "${USE_ALT}" ]]; then
  TIME_HINT="$(printf '%s' "${TIME_TEXT}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${TIME_HINT}" == *"noon"* || "${TIME_HINT}" == *"12"* || "${TIME_HINT}" == *"afternoon"* ]]; then
    USE_ALT="alt"
  fi
fi

mkdir -p "${TARGET_DIR}"
mkdir -p "${ASSETS_DIR}"

if [[ ! -f "${ASSETS_DIR}/README.md" ]]; then
  cat > "${ASSETS_DIR}/README.md" <<'EOF'
This folder holds venue-specific assets for Neon Blonde.
Put flyers, logos, photos, and reference graphics here.
EOF
fi

if [[ ! -f "${NOTES_PATH}" ]]; then
  printf "Venue: %s\nDate: %s\nTime: %s\n" "${VENUE_NAME}" "${VENUE_DATE}" "${TIME_TEXT}" > "${NOTES_PATH}"
fi

if [[ "${USE_ALT}" == "alt" ]]; then
  cli-anything-gimp project venue-template \
    --venue "${VENUE_NAME}" \
    --date "SAT 5-10" \
    --time "${TIME_TEXT}" \
    --alt-size \
    --output "${PROJECT_PATH}"
else
  cli-anything-gimp project venue-template \
    --venue "${VENUE_NAME}" \
    --date "SAT 5-10" \
    --time "${TIME_TEXT}" \
    --output "${PROJECT_PATH}"
fi

echo "Created venue package at: ${TARGET_DIR}"
