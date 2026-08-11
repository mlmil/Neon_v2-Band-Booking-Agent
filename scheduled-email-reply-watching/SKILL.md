---
name: scheduled-email-reply-watching
description: Watch a Gmail thread for a client's reply and execute pre-approved follow-up actions (notify Mike, DM band members) via checkpointed cron scripts with honest address parsing and delivery receipts.
---

# Scheduled Email Reply Watching

Use when you've sent a client an approved question (e.g., asking for a gig address or time) and Mike wants automatic action when the reply lands — typically: notify Mike, and/or fire pre-approved Telegram DMs to band members.

## When to use

- "Send and monitor for reply" requests where a follow-up action is pre-approved.
- Missing gig detail (street address, exact time) that was requested from the client by email.
- Any request to "shoot [members] the address/time on Telegram as soon as it arrives."

## Build the watcher script

Place under `~/.hermes/profiles/neon-v2/scripts/` so cron's relative `script` path resolves. Example in production: `mory_address_watch.py` (job name "Mory address watch + member DMs").

1. **Edge-triggered checkpoint** — state JSON with `seen` and `sent` maps keyed by IMAP message UID. On FIRST run, snapshot all existing messages from the sender and stay silent (empty stdout). Later runs process only unseen UIDs. This prevents re-processing the whole thread history.
2. **IMAP read-only** — `BODY.PEEK`, `INBOX` readonly, search `FROM <client-email>` since a boundary date. Never change read state.
3. **Address parsing, in order**: street regex (`\d{1,6} ... Street|Ave|Rd|Dr|Ln|Ct|Way|...`), CA zip (`93\d{3}`) appended to the street match, maps URL (`maps.google.com|goo.gl|maps.app.goo.gl`), then a line containing "address is / located at / we are at" as fallback.
4. **Action on address found** — send pre-approved Telegram DMs (see `telegram-outbound-messaging`), record per-recipient message IDs in state `sent`, print a JSON confirmation (delivered to Mike).
5. **If a new reply lacks a parseable address** — print `REPLY_NO_ADDRESS` with a body preview. Never guess an address, never auto-send a wrong one.

## Cron setup

- Use `every 10m`, NOT bare `10m`. A bare `10m` schedule creates a ONE-SHOT job (`repeat: once`); `every 10m` gives `repeat: forever`. Verify `"repeat": "forever"` in the job listing after create — if it says `once`, remove and recreate.
- `no_agent: true` + script: empty stdout = silent tick; non-empty stdout delivered verbatim; non-zero exit sends an error alert (so a broken watcher can't fail silently).
- `deliver` defaults to origin chat — correct for Mike's private alerts.

## Telegram DM mechanism

- Member IDs: `~/.hermes/profiles/<profile>/platforms/pairing/telegram-approved.json` — `user_id → user_name`. Always resolve IDs from this file or the gateway, never from typed-in message text.
- Bot token: `TELEGRAM_BOT_TOKEN` in the profile `.env`. Call `https://api.telegram.org/bot<token>/sendMessage` with `chat_id` = user_id.
- Approved members example (neon-v2 profile): Mike `7118814432`, Curtis `8983141338`, Kyle `8678658805`, Dave `8876608482`, Alfred (Telegram name "Sin Chonies") `8934145331`. Verify with `telegram_dm_test.py --dry-run` before arming.

## Approval gate (mandatory)

Get Mike's explicit approval of the EXACT DM wording and recipient list BEFORE arming the watcher. Per-recipient variants are allowed in one approval (e.g., Dave gets "6:00 is fine", others get "be there 5:00"). Any wording change after approval invalidates it — re-approve.

## Pitfalls

- First-run snapshot must complete before arming the cron, or the watcher replays the entire thread (and may spam DMs or alerts).
- If the client replies with an address in a photo/attachment, the text parser will miss it — the REPLY_NO_ADDRESS alert to Mike is the correct fallback, then forward/type the address manually.
- Keep the watcher's state file under the profile cron state dir; a fresh clone without it will re-snapshot and stay silent (safe), not replay.
