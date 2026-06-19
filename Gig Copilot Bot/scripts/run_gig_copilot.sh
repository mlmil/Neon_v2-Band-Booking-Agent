#!/bin/zsh
set -euo pipefail

LANE_ROOT="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot"
TOKEN_FILE="${GIG_COPILOT_TOKEN_FILE:-$HOME/.hermes/secure/gig_copilot_neon_bot_token.txt}"
STATE_FILE="${GIG_COPILOT_STATE_FILE:-$HOME/.hermes/gig_copilot_neon_state.json}"
PROFILES_FILE="${GIG_COPILOT_PROFILES_FILE:-$HOME/.hermes/gig_copilot_neon_profiles.json}"
RECEIPT_FILE="${GIG_COPILOT_RECEIPT_FILE:-$HOME/.hermes/gig_copilot_neon_group_receipts.json}"
GROUP_CHAT_ID="${GIG_COPILOT_GROUP_CHAT_ID:--1004424634571}"
PYTHON_BIN="${GIG_COPILOT_PYTHON:-/opt/homebrew/bin/python3}"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

if [ -f "$HOME/.zshenv" ]; then
  set -a
  source "$HOME/.zshenv"
  set +a
fi

cd "$LANE_ROOT"
exec "$PYTHON_BIN" -m gig_copilot_bot run --token-file "$TOKEN_FILE" --state-file "$STATE_FILE" --profiles-file "$PROFILES_FILE" --enable-gig-day-updates --group-chat-id "$GROUP_CHAT_ID" --receipt-file "$RECEIPT_FILE"
