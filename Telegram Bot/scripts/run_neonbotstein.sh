#!/bin/zsh
set -euo pipefail

LANE_ROOT="/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot"
NEON_BLONDE_ROOT="${NEON_BLONDE_ROOT:-/Volumes/VADER/Manifold/Neon_Blonde}"
TOKEN_FILE="${NEONBOTSTEIN_TOKEN_FILE:-$HOME/.hermes/secure/neon_bot_token.txt}"
STATE_FILE="${NEONBOTSTEIN_STATE_FILE:-$HOME/.hermes/neonbotstein_state.json}"
PYTHON_BIN="${NEONBOTSTEIN_PYTHON:-/opt/homebrew/bin/python3}"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export NEON_BLONDE_ROOT

cd "$LANE_ROOT"
exec "$PYTHON_BIN" -m telegram_bot run --token-file "$TOKEN_FILE" --state-file "$STATE_FILE"
