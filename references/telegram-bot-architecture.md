# Telegram Bot Architecture — Neon V2 and Co-Pilot

## Current Setup (July 2026)

The old @Neonbandman_bot (ID 8502223057) has been **deleted**. All remnants
(old token files, launchd plists, logs, scripts) were cleaned up on 2026-07-07.

The active bots are **@neonblondebot** (`neon-v2`) and **@GigCopilotNeon_Bot** (`neon-co_pilot`).

- Tokens: profile-local `TELEGRAM_BOT_TOKEN` values in each Hermes profile `.env`
- Connected through profile-specific Hermes Gateway launchd services
- Group chats: Full read access (privacy mode disabled via BotFather)
- Authorized Neon Blonde group: `-1004424634571`
- Ordinary unmentioned group messages are observed as context; routine chatter does not trigger a reply.

## Hermes Gateway

The bot runs as part of the Hermes gateway, not as a standalone script.
- Launchd services: `ai.hermes.gateway-neon-v2` and `ai.hermes.gateway-neon-co_pilot`
- Gateway profiles: `neon-v2` and `neon-co_pilot`
- Env vars: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`

## Direct API Calls (for standalone scripts)

| Service | Method | Credentials |
|---|---|---|
| Neon Blonde calendar | Fetch the public iCal feed | None (public, read-only) |
| Mark's Freshground calendar | Fetch public iCal feed + parse VEVENT blocks | None (public feed) |
| Gmail IMAP | `imaplib.IMAP4_SSL` with `BODY.PEEK` | `$NEON_SMTP_CONFIG` (app password) |
| Telegram | Hermes Gateway / Bot API | Profile-local `TELEGRAM_BOT_TOKEN` |

## Operational Contradiction Monitoring

Load `communications-triage.md` for the active monitoring contract. The bot compares operational claims in the authorized group against the published Band Sheet. It remains silent on routine chatter and alerts when it sees a time, date, venue, cancellation, money, availability, or logistics claim that conflicts with the current source of truth or needs Mike's action.

## Pitfalls Encountered

1. **Hermes subprocess**: Don't do it. MCP tools won't connect. Use direct API calls.
2. **Multiple services**: Inspect `hermes gateway list` and restart only the affected profile gateway.
3. **Telegram Markdown**: Unmatched `*` or `_` causes 400 errors. Always catch and retry without parse_mode.
4. **Old bot cleanup**: If migrating bots, delete old token files from `~/.hermes/secure/`, remove old launchd plists, and update all reference docs. The state DB may retain old bot IDs but won't cause issues.
