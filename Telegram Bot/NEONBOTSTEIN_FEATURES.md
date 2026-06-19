# NeonBotstein Features

Bot: `NeonBotstein_Bot`
Role: Neon Blonde band-ops and logistics coordination bot
Status: live via launchd on `studio_hub`

## Short Description

NeonBotstein handles Neon Blonde gigs, logistics, availability, rehearsals, and
booking status from the live Band Sheet.

## Live Telegram Commands

### `/help`

Shows the currently supported read-only commands.

Current reply includes:

- `/gigs`
- `/status`
- `/members-out`
- `/this-week`
- `/free`
- `/venue <name>`
- `/rehearsals`
- `/closeout`
- `/chatid`
- `/help`

### `/gigs`

Lists upcoming booked gigs from the live Band Sheet JSON feed.

For each parsed gig, it can show:

- Date
- Start time
- Venue name
- City, when the Band Sheet provides one

If the Band Sheet source is stale, the reply adds a warning that the view should
be treated as draft-only until manual verification.

### `/status`

Reports Band Sheet freshness.

It shows:

- Whether the Band Sheet source is fresh or stale
- The source update date
- How many days old the source is
- A manual-verification warning when stale

### Unknown Messages

For unsupported text, the bot stays inside its current safe scope and tells the
user it can only answer read-only Band Sheet questions right now.

### `/members-out`

Shows member availability notes from the Band Sheet snapshot.

### `/this-week`

Shows this week's Band Sheet notes.

### `/free`

Shows Band Sheet open dates and includes freshness context so Mike can see
whether the source is current or needs manual verification.

### `/venue <name>`

Searches upcoming Band Sheet gigs by venue, city, or raw gig summary substring.

Examples:

```text
/venue leashless
/venue yacht
/venue santa barbara
```

### `/rehearsals`

Shows upcoming Neon rehearsals from Mark's Freshground public iCal feed.

The lookup is read-only and converts UTC calendar entries to Pacific time before
grouping by day.

### `/closeout`

Shows a read-only summary of post-gig queue items that need closeout.

It reads the local queue CSV and does not mark anything closed.

### `/chatid`

Replies with the current Telegram chat ID. Use this inside the official band
group when configuring band-wide announcements.

## Current Data Capabilities

### Band Sheet Snapshot

The bot can fetch and normalize the public Band Sheet JSON endpoint:

```text
https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json
```

Normalized snapshot fields include:

- Source URL
- Fetch timestamp
- Band Sheet updated timestamp
- Freshness age in days
- Stale/fresh status
- Booked gigs
- Free weekends text
- Members-out text
- This-week notes
- Provider warnings

### Booked Gig Parsing

For booked gig lines, the bot tries to parse:

- Date
- Start time
- Venue name
- City

If a gig line does not match the expected shape, the bot preserves the original
summary instead of inventing fields.

### Freshness Guard

The bot treats Band Sheet data older than four days as stale.

Stale data can either:

- Return a snapshot with a blocking warning
- Fail closed when `--fail-on-stale` is used

## Logistics Coordination Scope

The bot is intended to support Neon Blonde logistics coordination around:

- Upcoming gig visibility
- Schedule freshness checks
- Member availability notes from Band Sheet text
- Rehearsal context, as future sources are wired in
- Booking and logistics status checks, as future intent handlers are added

Current live implementation is intentionally narrower:

- It answers `/gigs`
- It answers `/status`
- It answers `/members-out`
- It answers `/this-week`
- It answers `/free`
- It searches `/venue <name>`
- It reads Freshground rehearsal context for `/rehearsals`
- It reads the local post-gig queue for `/closeout`
- It checks Band Sheet freshness
- It keeps all responses read-only

Future logistics features should preserve the Neon V2 safety model:

- Calendar reads use public/read-only sources
- Calendar writes stay manual
- Availability claims require two-pass verification
- Venue-facing messages require Mike approval
- Booking confirmation and payment status changes require Mike approval

## Operator And Admin Features

### Health Check

Command:

```bash
python3 -m telegram_bot health
```

Checks that the configured Telegram token belongs to:

```text
NeonBotstein_Bot
```

Common failure states:

- `HTTP 401` - token rejected by Telegram
- `wrong bot: ...` - token belongs to another bot
- `HTTP 409` - another Telegram poller or webhook is already active

### Local Reply Simulation

Command:

```bash
python3 -m telegram_bot reply /gigs
python3 -m telegram_bot reply /status
```

This tests reply behavior without sending Telegram messages.

### Single Poll Cycle

Command:

```bash
python3 -m telegram_bot poll-once
```

Processes one Telegram long-poll cycle and exits.

Useful for:

- Checking live token behavior
- Confirming update handling
- Debugging without starting a daemon

### Foreground Run Loop

Command:

```bash
python3 -m telegram_bot run
```

Runs the Telegram polling loop in the foreground.

Bounded debug mode:

```bash
python3 -m telegram_bot run --max-cycles 1 --sleep-seconds 0
```

### Launchd Service

Installed LaunchAgent:

```text
com.neonblonde.neonbotstein
```

Launchd wrapper:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot/scripts/run_neonbotstein.sh
```

Launchd plist:

```text
/Users/studio_hub/Library/LaunchAgents/com.neonblonde.neonbotstein.plist
```

Repo template:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot/launchd/com.neonblonde.neonbotstein.plist
```

### Runtime State

Telegram offset state:

```text
/Users/studio_hub/.hermes/neonbotstein_state.json
```

Logs:

```text
/Users/studio_hub/.hermes/logs/neonbotstein.log
```

Token file:

```text
/Users/studio_hub/.hermes/secure/neon_bot_token.txt
```

Do not print or commit token values.

## Safety Features

The bot currently avoids protected writes.

It does not directly:

- Update Google Calendar
- Publish Band Sheet changes
- Send venue-facing email
- Update WordPress
- Share venue portal files
- Change booking or pay terms
- Mark payment complete

It is built around read-only checks and explicit operator commands.

## Reliability Features

- Telegram update offsets are persisted after processing.
- Telegram HTTP failures are wrapped without exposing token details.
- Markdown parsing is not used for sends yet, avoiding Telegram parse-mode errors.
- Unit tests use fixtures instead of live network calls.
- Launchd wrapper pins Homebrew Python to avoid macOS Python 3.9 `StrEnum` failure.
- Health check validates bot identity before relying on a token.

## Test Coverage

Current tests cover:

- Repo/lane discovery
- Band Sheet parsing
- Band Sheet freshness warnings
- CLI snapshot and reply commands
- Telegram transport polling and sending behavior
- Telegram identity checks
- Safe HTTP error handling
- Launchd wrapper and plist assets

Verification command:

```bash
python3 -m unittest discover -s tests
```

Current verified result:

```text
32 tests passed
```

## Feature Roadmap

Good next additions:

- Add richer `/help` examples for natural-language forms
- Add richer natural-language forms beyond the current examples

Features that need extra safety work:

- Availability answers need two-pass verification
- Calendar-derived claims need public iCal cross-checking
- Venue replies need draft/approval flow
- Any source-of-truth updates need Mike approval
