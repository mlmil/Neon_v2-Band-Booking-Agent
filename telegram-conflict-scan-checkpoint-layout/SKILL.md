---
name: telegram-conflict-scan-checkpoint-layout
description: Documents the actual checkpoint and script layout used by the Neon V2 Telegram conflict scan deployment.
---

# Telegram Conflict Scan Checkpoint Layout

This skill records the actual deployment layout of the Neon V2 Telegram conflict scan, which differs from the generic `scheduled-telegram-conflict-scans` skill's documented paths.

## Checkpoint

- **Path**: `checkpoints/telegram_conflict_scan.json` (relative to the Neon V2 skill root at `/Users/cthulhu/Desktop/Skill FIles/Neon_v2/`)
- **Fields**:
  - `last_check` / `scan_attempt` — ISO timestamp of the last scan
  - `last_update_id` — Telegram API update_id for incremental fetching (absent on first run; script handles gracefully by fetching latest 50)
  - `new_messages_found` — boolean flag from the most recent scan

## Script

- **Path**: `scripts/telegram_conflict_scan.py`
- **Mechanism**: Calls Telegram Bot API `getUpdates` with incremental offset tracking, filters for `-1004424634571`, persists checkpoint
- **Output**:
  - `NO_NEW_UPDATES` — no pending updates at all
  - `NO_GROUP_MESSAGES` — updates exist but none target the authorized group
  - `FOUND N message(s)` — new group messages with sender and text preview

## Environment

- **Cron runtime**: `TELEGRAM_BOT_TOKEN` is automatically populated
- **Manual/terminal runs**: Source from profile `.env`:
  ```bash
  set -a && source ~/.hermes/profiles/neon-v2/.env && set +a
  ```

## Relationship to class skill

The class skill `scheduled-telegram-conflict-scans` documents a generic `data/telegram/checkpoint.json` path. The actual Neon V2 deployment uses `checkpoints/telegram_conflict_scan.json` with the script-driven workflow above.
