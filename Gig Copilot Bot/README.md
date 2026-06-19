# Gig Copilot Bot

Separate Mike-only test bot for Neon Blonde day-of-show logistics.

Bot username:

```text
GigCopilotNeon_Bot
```

## Scope

- Talks to Mike for setup/testing
- Sends one band-group logistics update on gig days
- Stores Mike onboarding/profile data in local JSON
- Simulates show-day logistics messages
- Uses Gemini for freeform Mike-only copilot replies when a Gemini key is available
- Does not update Calendar, Band Sheet, WordPress, email, or payments

## Files

- Package: `gig_copilot_bot/`
- Tests: `tests/`
- Profile JSON: `/Users/studio_hub/.hermes/gig_copilot_neon_profiles.json`
- Token file: `/Users/studio_hub/.hermes/secure/gig_copilot_neon_bot_token.txt`
- State file: `/Users/studio_hub/.hermes/gig_copilot_neon_state.json`
- Group-send receipts: `/Users/studio_hub/.hermes/gig_copilot_neon_group_receipts.json`
- Band group chat ID: `-1004424634571`
- Gemini key: environment `GEMINI_API_KEY` or `GOOGLE_API_KEY`, with optional file fallback `/Users/studio_hub/.hermes/secure/gemini_api_key.txt`

## Commands

Run local replies without Telegram:

```bash
python3 -m gig_copilot_bot reply /start
python3 -m gig_copilot_bot reply /onboard
python3 -m gig_copilot_bot reply /profile
python3 -m gig_copilot_bot reply /simulate-show-day
python3 -m gig_copilot_bot reply /status
python3 -m gig_copilot_bot reply "What should I do before a show?"
python3 -m gig_copilot_bot gig-day-update --dry-run
```

Verify Telegram identity:

```bash
python3 -m gig_copilot_bot health
```

Process one Telegram polling cycle:

```bash
python3 -m gig_copilot_bot poll-once
```

Run tests:

```bash
python3 -m unittest discover -s tests
```

## Onboarding

V1 `/onboard` saves Mike's default logistics profile:

- Name: Mike
- Role: Bass + PA setup
- Default origin: Ventura
- Alternate origins: Oxnard, Santa Barbara
- Standard arrival: 60 minutes before start
- PA/load-in arrival: 120 minutes before start
- Live location required: yes

This is intentionally simple for the first Mike-only test.

## Gemini Behavior

Fixed commands such as `/onboard`, `/profile`, `/status`, and
`/simulate-show-day` stay deterministic.

Freeform messages are sent to Gemini with a Mike-only safety prompt. Gemini is
not allowed to claim it sent band messages or changed Calendar, Band Sheet,
email, WordPress, payments, or member data.

## Gig-Day Group Updates

The launchd service runs with `--enable-gig-day-updates`. On each loop it checks
the public Neon calendar for gigs dated today. If it finds one, it sends one
plain logistics check-in to the band group and records a local receipt so the
same gig is not sent twice.

The message is informational only. It does not confirm booking changes, edit
Calendar, publish the Band Sheet, send email, update WordPress, or mark payments.
