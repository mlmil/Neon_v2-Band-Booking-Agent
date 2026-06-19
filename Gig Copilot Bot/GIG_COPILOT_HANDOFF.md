# Gig Copilot Neon Handoff

Bot: `GigCopilotNeon_Bot`
Lane: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot`
Mode: Mike setup plus gig-day band-group logistics updates

## Purpose

Gig Copilot is the separate day-of-show logistics copilot for Neon Blonde. It
answers Mike privately and sends one logistics check-in to the band group on gig
days.

## Safety

Band group messages are allowed only for gig-day logistics updates to chat
`-1004424634571`.
Do not update Google Calendar, Band Sheet, WordPress, email, venue assets, or
payments.

## Credentials

Token path:

```text
/Users/studio_hub/.hermes/secure/gig_copilot_neon_bot_token.txt
```

Do not print, commit, or summarize token values.

## State

Profile JSON:

```text
/Users/studio_hub/.hermes/gig_copilot_neon_profiles.json
```

Telegram offset state:

```text
/Users/studio_hub/.hermes/gig_copilot_neon_state.json
```

Band-group send receipts:

```text
/Users/studio_hub/.hermes/gig_copilot_neon_group_receipts.json
```

## Commands

```bash
cd "/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot"
python3 -m unittest discover -s tests
python3 -m gig_copilot_bot health
python3 -m gig_copilot_bot reply /onboard
python3 -m gig_copilot_bot reply /profile
python3 -m gig_copilot_bot reply /simulate-show-day
python3 -m gig_copilot_bot poll-once
python3 -m gig_copilot_bot gig-day-update --dry-run
```

## Current V1 Capabilities

- `/start`
- `/help`
- `/onboard`
- `/profile`
- `/simulate-show-day`
- `/status`
- Freeform Mike-only logistics questions powered by Gemini when a Gemini key is available
- Gig-day band-group logistics update, deduped by local receipt

## Next Good Step

Use `gig-day-update --dry-run` to preview today's band-group message. The
launchd service runs the same check automatically.

## Gemini

Freeform replies use Gemini through `gig_copilot_bot/gemini_provider.py`.

Key lookup order:

1. `GEMINI_API_KEY`
2. `GOOGLE_API_KEY`
3. `/Users/studio_hub/.hermes/secure/gemini_api_key.txt`

The default model is `gemini-2.5-flash` with thinking disabled for short bot
responses. Fixed commands do not call Gemini.
