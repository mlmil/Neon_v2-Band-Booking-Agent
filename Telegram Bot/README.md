# Telegram Bot

`NeonBotstein_Bot` is the read-only Telegram operations bot for Neon V2.

Current scope:

1. Discover the lane and repo context safely.
2. Parse the public BandSheet JSON feed.
3. Normalize booked gigs and freshness warnings.
4. Watch Telegram booking chatter for calendar-attention flags.
5. Archive watcher state locally without editing Google Calendar.
6. Send high-priority internal AgentMail flag reports to Mike and Alfred.
7. Answer read-only free-form band questions through Gemini when addressed as
   `@neon` in a group chat.

Approved filesystem root:

```text
/Volumes/VADER/Manifold/Neon_Blonde
```

The launch wrapper exports this as `NEON_BLONDE_ROOT`. The running bot has
macOS read/write access there as `studio_hub`. Calendar, Band Sheet, email,
WordPress, and payment mutations still follow Neon V2 protected-action rules.

Run the read-only snapshot check:

```bash
python3 -m telegram_bot bandsheet-snapshot
```

Run it against the local fixture:

```bash
python3 -m telegram_bot bandsheet-snapshot --fixture fixtures/bandsheet-data.sample.json
```

Simulate a read-only bot reply without Telegram transport:

```bash
python3 -m telegram_bot reply /gigs
python3 -m telegram_bot reply /status
python3 -m telegram_bot reply /members-out
python3 -m telegram_bot reply /this-week
python3 -m telegram_bot reply /free
python3 -m telegram_bot reply "/venue leashless"
python3 -m telegram_bot reply /rehearsals
python3 -m telegram_bot reply /closeout
python3 -m telegram_bot reply /drafts
python3 -m telegram_bot reply "show me the draft"
python3 -m telegram_bot reply /flags
python3 -m telegram_bot reply /watch-status
```

In a Telegram group, use `@neon` to ask a free-form read-only question:

```text
@neon what is the next gig?
@neon are we free next Friday?
@neon what time is the Yacht Club show?
```

The free-form answer path is read-only. It may summarize Band Sheet context, but
it must not edit Calendar, send email, publish Band Sheet changes, update
WordPress, or mark payments.

Booking watcher commands:

```text
/flags - show open Calendar Attention Queue items
/flag <id> - show one queued item with source context
/reviewed <id> - mark an item reviewed after Mike handles it manually
/dismiss <id> - dismiss a false positive
/watch-status - show watcher storage status
/drafts - list pending AgentMail drafts
/draft - show the current pending AgentMail draft
```

Natural-language forms such as `show me the drafts`, `AgentMail`, and
`show me the email from Philip` go through the stateful Gemini Neon V2 agent.
Gemini reads the actual incoming email, checks Calendar context, maintains the
conversation, and can create or revise a versioned draft.

The draft must be displayed before the live Telegram agent can send it. Local CLI
previews cannot send. Unanswered drafts trigger a reminder after two hours and
then daily. Explicit `/draft` and `/drafts` remain legacy read-only shortcuts.

Booking watcher state lives under:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/data/telegram/booking_watcher/
```

Boundary: the watcher may alert the band about possible booking, cancellation,
reschedule, time, venue, or availability issues. It does not create, edit, or
delete Google Calendar events. Mike remains the only Calendar editor.

High-priority flags also send an internal AgentMail report from
`neon_blonde@agentmail.to` to:

- `neonblondevc@gmail.com`
- `sin.chonies.inc@gmail.com`

If AgentMail is unavailable, the Telegram alert and local queue still work.

To find a Telegram group ID, send this in the group:

```text
/chatid
```

Check the configured Telegram bot identity:

```bash
python3 -m telegram_bot health
python3 -m telegram_bot health --env-file ~/.hermes/.env
```

Process one Telegram long-poll cycle:

```bash
python3 -m telegram_bot poll-once
```

Run the polling loop in the foreground:

```bash
python3 -m telegram_bot run
```

Run a bounded foreground check:

```bash
python3 -m telegram_bot run --max-cycles 1 --sleep-seconds 0
```

Launchd assets are present but not installed automatically:

```bash
cp launchd/com.neonblonde.neonbotstein.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.neonblonde.neonbotstein.plist
```

Current live credential status:

1. `~/.hermes/secure/neon_bot_token.txt` identifies `NeonBotstein_Bot`.
2. `python3 -m telegram_bot health` should return `ok: NeonBotstein_Bot`.
3. Do not print or commit token values.

Out of scope for this milestone:

1. Live routing
2. Automatic Calendar writes
3. Band Sheet publishing
4. Invented location or scheduling data
