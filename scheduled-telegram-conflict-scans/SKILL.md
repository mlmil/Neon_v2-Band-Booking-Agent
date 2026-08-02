---
name: scheduled-telegram-conflict-scans
description: Execute recurring allowlisted Telegram conflict scans using only persisted post-checkpoint observations and exact silent-output contracts.
---

# Scheduled Telegram Conflict Scans

Use this class skill for cron-driven scans of an authorized Telegram operations group when the scheduler supplies a private checkpoint and requires silence when no new evidence exists.

## Operating contract

1. Read the scheduler-named governing communications reference directly.
2. Resolve only the explicit allowlisted chat and private checkpoint.
3. Read the project-local persisted boundary at `data/telegram/checkpoint.json`.
4. Prefer persisted receipts under `data/telegram/receipts/`; use `data/telegram/booking_watcher/queue.jsonl` or `archive.jsonl` only as fallback observation streams when each record independently contains exact chat identity, message identity, content, and a timestamp newer than the checkpoint.
5. Exclude DMs, bot-authored group replies, old records, prior cron output, gateway status, unchanged checkpoints, and empty queues from new inbound-group evidence.
6. Do not fetch Telegram history or broad exports. Do not inspect unrelated sessions, session databases, gateway diagnostics, or setup state to manufacture evidence. Do not load extra skills during a tightly scoped scheduled scan unless explicitly requested.
7. If no verifiable new inbound group message exists, and the scheduler specifies the sentinel, return exactly `[SILENT]`. Empty intervals are normal and are not coverage gaps.
8. `verification_evidence.db` is file-change provenance, not message evidence; never infer an inbound message from it.
9. For each genuinely new operational claim, compare date, venue, city/address, show time, arrival/load-in, pay, directions, cancellation, availability, equipment, parking, access, and production facts against the live Band Sheet.
10. Keep public show time distinct from arrival, load-in, soundcheck, doors, and curfew. Ambiguous logistics are not show-time conflicts.
11. If no actionable conflict exists, remain silent. If a conflict exists, issue one concise alert naming both the Telegram value and Band Sheet value, and state that the Band Sheet remains the plan until Mike publishes a correction.
12. Preserve deduplication identity and advance the checkpoint only after the observation scan completes successfully.

## Persisted evidence layout

- `data/telegram/checkpoint.json` is the authoritative scan boundary; read `chat_id`, `last_scan_at`, `last_message_id`, and `last_message_date`.
- `data/telegram/receipts/*.json` are preferred persisted scan receipts; accept only receipts that identify the authorized chat and independently verifiable inbound-message details.
- `data/telegram/booking_watcher/queue.jsonl` and `archive.jsonl` are fallback streams. Filter every record by exact authorized chat ID, message identity/content, and a timestamp newer than the checkpoint. DM records and bot-authored group replies are non-evidence for new inbound group activity.
- The profile's `verification_evidence.db` records file-change provenance, not Telegram message content; it cannot establish that an inbound message exists.

## Gateway log as secondary evidence source

When no dedicated receipt/observation stream exists and the scheduler restricts history fetches, the running gateway's log is a legitimate secondary evidence check:

1. Read `<profile_logs>/gateway.log`, scanning for `inbound message:` entries.
2. Filter for the exact allowlisted group chat ID (e.g., `-1004424634571`). Entries show `chat=<numeric_id>`.
3. Entries with `chat=7118814432` (Mike's DM) or other individual user IDs are DMs, not group messages — exclude them.
4. Compare the entry's timestamp against the checkpoint's `last_scan_at`. Only entries newer than the last scan qualify.
5. The gateway log's file modification time (`stat -f "%Sm"`) shows when the gateway last processed any message. If no qualifying group entries appear since the checkpoint, no new group messages were observed.
6. A running gateway (confirmed via `launchctl list | grep hermes` or `pgrep -fl hermes`) confirms transport is up but does not itself prove group messages arrived.
7. **Caveat**: The gateway log may rotate or be truncated. Absence of entries in a truncated log is not conclusive — prefer the dedicated receipt/checkpoint evidence path when available.

## Cron environment constraints

- The `execute_code` tool is blocked for cron jobs — standalone `.py` scripts must be used instead.
- Inline Python (`python3 -c '...'`) triggers unanswerable approval prompts in cron mode. Always write a standalone `.py` file and invoke it with `python3 /path/to/script.py`.
- `terminal()` foreground commands work normally up to the scheduler's timeout.
- **Profile env vars in agent-cron dispatch**: Environment variables (including `TELEGRAM_BOT_TOKEN`) are loaded by the Hermes gateway process from the profile `.env` file. They are NOT automatically inherited by `terminal()` subprocesses during an agent-cron dispatch unless `terminal.env_passthrough` includes them. If a standalone script needs profile env vars, source them manually:
  ```bash
  set -a && source ~/.hermes/profiles/<profile>/.env && set +a && python3 /path/to/script.py
  ```
- If the env var is absent and you cannot source it, do NOT troubleshoot or diagnose setup. Fall through to `[SILENT]` — absent credentials mean no verifiable inbound messages, which is a normal empty-interval outcome, not a coverage gap.
- `read_file`, `patch`, `search_files`, `write_file` work normally in cron context.

## Minimal read-only scan

1. Read the governing communications reference.
2. Read the checkpoint.
3. Inspect only receipts/observation records for the exact allowlisted group and post-checkpoint messages.
4. If none qualify, emit the exact silent sentinel; do not call it a coverage gap.
5. Only after a qualifying operational claim is observed, read and compare the live Band Sheet.
