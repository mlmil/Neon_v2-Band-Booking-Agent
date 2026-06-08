# Telegram Bot Architecture — Neon @Neonbandman_bot

## Design Decision: Direct API calls vs Hermes subprocess

**Tried first**: `hermes chat -q "<query>" -s Neon_v1 -Q` spawned as a Python subprocess.

**Result**: Hung indefinitely. The Hermes CLI session tries to connect to MCP servers (Desktop Commander, CamoFox browser, Google Workspace MCPs) that aren't available in the subprocess context. The subprocess call never returned.

**Working approach**: Standalone Python script that makes direct API calls:

| Service | Method | Credentials |
|---|---|---|
| Neon Blonde calendar | `google.oauth2.credentials.Credentials` + `googleapiclient` | `~/.hermes/neon_oauth_token.json` |
| Mark's Freshground calendar | Fetch public iCal feed + parse VEVENT blocks | None (public feed) |
| Gmail IMAP | `imaplib.IMAP4_SSL` | `~/.hermes/skills/Neon_v1/smtp_config.json` (app password) |
| AgentMail send | REST API `POST /v0/inboxes/{id}/messages/send` | `AGENTMAIL_API_KEY` from `~/.zshenv` |
| Telegram | Bot API `api.telegram.org/bot{token}/...` | `~/.hermes/secure/neon_bot_token.txt` |

## Launchd Setup

- Plist: `~/Library/LaunchAgents/com.neonblonde.bot.plist`
- Uses `/opt/homebrew/bin/python3` (homebrew, not macOS system Python)
- `-u` flag for unbuffered stdout
- `KeepAlive` = true (auto-restart on crash)
- `RunAtLoad` = true (auto-start on boot)
- Logs to `~/.hermes/logs/neon_bot.log` (both stdout and stderr)

## Telegram Polling Details

- Long-poll with `timeout=30` (reduces empty responses)
- Poll interval: 5 seconds between request cycles
- Offset tracking via `~/.hermes/neon_bot_state.json`
- Send `sendChatAction("typing")` before processing long requests
- Markdown parsing: try with `parse_mode="Markdown"` first, fall back to plain text on 400 error

## Pitfalls Encountered

1. **Hermes subprocess**: Don't do it. MCP tools won't connect. Use direct API calls.
2. **Python version**: launchd uses /opt/homebrew/bin/python3 (3.14). System Python 3.9 has google-auth deprecation warnings.
3. **Multiple stale processes**: `hermes` processes from previous sessions accumulate. Kill them with `pkill -f hermes` before debugging.
4. **Telegram Markdown**: Unmatched `*` or `_` causes 400 errors. Always catch and retry without parse_mode.
