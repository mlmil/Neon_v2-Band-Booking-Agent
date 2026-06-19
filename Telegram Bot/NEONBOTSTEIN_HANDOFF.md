# NeonBotstein Bot Handoff

Last verified: 2026-06-16
Repo: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2`
Lane: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot`
Bot username: `NeonBotstein_Bot`
LaunchAgent label: `com.neonblonde.neonbotstein`

## Purpose

NeonBotstein is the Neon Blonde band-ops and logistics coordination Telegram bot.
It gives Mike quick read-only answers from the live Band Sheet, including gigs,
schedule freshness, member availability notes, rehearsal context, and booking or
logistics status checks.

## Authority And Safety

Before working on this bot, load:

1. `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/SKILL.md`
2. `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/AGENT_COMPATIBILITY.md`
3. `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/references/automation-map.md`
4. `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/references/failure-handling.md`
5. `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/config/credential-manifest.json`

Do not expose, print, commit, summarize, or fingerprint token values. Report only
whether credentials are available, missing, unreadable, valid, or rejected.

Protected actions still require Mike approval:

- Send venue-facing email
- Publish Band Sheet changes
- Update WordPress
- Share venue portal files
- Change booking or pay terms
- Mark a payment complete
- Create, edit, or delete Google Calendar events

## Current Implementation

The bot is a small Python package under `Telegram Bot/`.

Key files:

- `telegram_bot/providers/bandsheet.py` - read-only Band Sheet JSON provider
- `telegram_bot/responder.py` - text-in/text-out reply logic
- `telegram_bot/telegram_transport.py` - Telegram API transport, polling, state
- `telegram_bot/cli.py` - CLI commands for health, replies, polling, and run loop
- `scripts/run_neonbotstein.sh` - launchd wrapper
- `launchd/com.neonblonde.neonbotstein.plist` - LaunchAgent template
- `tests/` - unit coverage for provider, responder, CLI, transport, and launch assets

Current supported commands:

```bash
cd "/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot"

python3 -m telegram_bot health
python3 -m telegram_bot reply /gigs
python3 -m telegram_bot reply /status
python3 -m telegram_bot poll-once
python3 -m telegram_bot run --max-cycles 1 --sleep-seconds 0
python3 -m unittest discover -s tests
```

Free-form group questions are routed through Gemini only when the message starts
with `@neon`. Private/direct messages may ask normal questions without the
trigger. The Gemini path is read-only and must stay inside the Neon V2 protected
action boundaries.

## Credential Contract

Primary token file:

```text
/Users/studio_hub/.hermes/secure/neon_bot_token.txt
```

Permissions should be restricted:

```bash
chmod 600 "$HOME/.hermes/secure/neon_bot_token.txt"
```

The file must contain the token for `NeonBotstein_Bot`. Do not use
`~/.hermes/.env` unless you intentionally pass `--env-file`; that file may point
to another Telegram bot used by Hermes.

Verify identity without printing token values:

```bash
python3 -m telegram_bot health
```

Expected output:

```text
ok: NeonBotstein_Bot
```

Common failures:

- `HTTP 401` - token is rejected by Telegram
- `wrong bot: ...` - token is valid but belongs to the wrong bot
- `HTTP 409` - another poller or webhook is consuming the same bot token

## Launchd Setup

Install or refresh the LaunchAgent:

```bash
cd "/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.hermes/logs"
chmod +x scripts/run_neonbotstein.sh
cp launchd/com.neonblonde.neonbotstein.plist "$HOME/Library/LaunchAgents/"
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.neonblonde.neonbotstein.plist" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.neonblonde.neonbotstein.plist"
launchctl enable "gui/$(id -u)/com.neonblonde.neonbotstein"
launchctl kickstart -k "gui/$(id -u)/com.neonblonde.neonbotstein"
```

Check service state:

```bash
launchctl print "gui/$(id -u)/com.neonblonde.neonbotstein" | sed -n '1,90p'
```

Healthy state should include:

```text
state = running
active count = 1
```

Check the active process:

```bash
pid=$(launchctl print "gui/$(id -u)/com.neonblonde.neonbotstein" | awk '/pid = / {print $3; exit}')
ps -p "$pid" -o pid=,command=
```

Expected process uses Homebrew Python:

```text
/opt/homebrew/.../Python -m telegram_bot run --token-file /Users/studio_hub/.hermes/secure/neon_bot_token.txt --state-file /Users/studio_hub/.hermes/neonbotstein_state.json
```

Logs:

```text
/Users/studio_hub/.hermes/logs/neonbotstein.log
```

State file:

```text
/Users/studio_hub/.hermes/neonbotstein_state.json
```

## Python Pitfall

Launchd starts with a minimal PATH. Plain `python3` resolves to macOS Python 3.9,
which fails because `enum.StrEnum` is unavailable:

```text
ImportError: cannot import name 'StrEnum' from 'enum'
```

The wrapper intentionally pins Python to:

```text
/opt/homebrew/bin/python3
```

Do not change `scripts/run_neonbotstein.sh` back to plain `python3` unless the
code is made Python 3.9 compatible first.

## Recreate From Scratch

1. Confirm repo and lane exist:

```bash
cd "/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot"
find . -maxdepth 2 -type f | sort
```

2. Restore or create token file:

```bash
mkdir -p "$HOME/.hermes/secure"
chmod 700 "$HOME/.hermes/secure"
# Add the NeonBotstein_Bot token to:
# /Users/studio_hub/.hermes/secure/neon_bot_token.txt
chmod 600 "$HOME/.hermes/secure/neon_bot_token.txt"
```

3. Verify code:

```bash
python3 -m unittest discover -s tests
python3 -m telegram_bot health
python3 -m telegram_bot reply /gigs --fixture fixtures/bandsheet-data.sample.json
```

4. Install launchd using the commands in `Launchd Setup`.

5. Verify launchd state and active process.

6. Send `/status` or `/gigs` to `NeonBotstein_Bot` in Telegram.

## Current Verified State

On 2026-06-16:

- `python3 -m telegram_bot health` returned `ok: NeonBotstein_Bot`
- launchd label `com.neonblonde.neonbotstein` reported `state = running`
- active process used Homebrew Python 3.14
- unit tests passed: `32/32`

## Recovery Commands

Restart service:

```bash
launchctl kickstart -k "gui/$(id -u)/com.neonblonde.neonbotstein"
```

Stop service:

```bash
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.neonblonde.neonbotstein.plist"
```

Run in foreground for debugging:

```bash
cd "/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot"
/opt/homebrew/bin/python3 -m telegram_bot run --max-cycles 1 --sleep-seconds 0
```

Check logs:

```bash
tail -n 80 "$HOME/.hermes/logs/neonbotstein.log"
```

## Notes For Future Agents

- Keep the bot read-only unless Mike explicitly approves a protected action.
- Preserve the `NeonBotstein_Bot` identity check in `telegram_bot/cli.py`.
- Do not run a second long-poller against the same Telegram token; HTTP 409 means
  another consumer is already active.
- Keep tests fast and fixture-based. Live Telegram checks should be explicit CLI
  commands, not unit tests.
- Remove generated `__pycache__` directories before preparing a clean diff.
