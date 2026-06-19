# Gig Copilot Neon Bot Design

Date: 2026-06-15
Bot: `GigCopilotNeon_Bot`
Lane: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot`

## Goal

Build a separate Mike-only test bot for Neon Blonde day-of-show logistics.

## Scope

V1 is not allowed to message the band or individual members other than Mike. It
uses Telegram only for Mike-facing onboarding and simulation.

## Commands

- `/start` - introduce the bot and point to onboarding
- `/help` - list commands
- `/onboard` - begin or continue Mike's onboarding quiz
- `/profile` - show Mike's saved logistics profile
- `/simulate-show-day` - send Mike a sample show-day logistics flow
- `/status` - show bot mode and profile storage status

## Profile Storage

Profiles are stored in local JSON:

```text
/Users/studio_hub/.hermes/gig_copilot_neon_profiles.json
```

No database is needed for v1.

## Mike Profile Fields

- `name`
- `role`
- `default_origin_city`
- `alternate_origin_cities`
- `standard_arrival_minutes`
- `pa_load_in_arrival_minutes`
- `live_location_required`

## Safety Rules

- Send only to Mike in v1.
- Do not send to the band group.
- Do not message Alfred, Dave, Curtis, Kyle, or Matt.
- Do not update calendars, Band Sheet, WordPress, payments, or email.
- Do not commit or print token values.

## Credential Path

The token should live at:

```text
/Users/studio_hub/.hermes/secure/gig_copilot_neon_bot_token.txt
```

## Launchd

Do not install launchd until the CLI and Mike-only bot flow pass local checks.

## Acceptance Criteria

- Unit tests pass.
- `/status` works locally through the responder.
- `/onboard` stores Mike's profile in JSON.
- `/profile` reads the stored profile.
- `/simulate-show-day` produces a Mike-only simulation with no external sends.
