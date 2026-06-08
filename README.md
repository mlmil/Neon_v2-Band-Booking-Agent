
# Neon_v1

Neon_v1 is the booking and rehearsal operations skill for Neon Blonde.

It handles:
- calendar availability checks with strict sanity rules
- rehearsal-date shortlists for the current week
- rehearsal reservation emails to Mark Antaky
- venue package creation for confirmed gigs
- GroupMe message sync and communication logging
- plain-language Band Sheet generation
- venue template support through a CLI-Anything GIMP harness

## Key paths

- Skill file: `SKILL.md`
- Persona: `NEON_V1_PERSONA.md`
- Booking workflow: `references/booking-workflow.md`
- Availability rules: `references/availability-verification.md`
- Band Sheet format: `references/band-sheet-format.md`
- GIMP harness spec: `references/gimp-harness-spec.md`
- Venue package script: `scripts/create_venue_package.sh`
- Rehearsal shortlist script: `scripts/find_rehearsal_dates.py`
- GroupMe sync script: `scripts/sync_groupme_messages.py`
- Calendar fetch script: `scripts/fetch_calendar_with_ranges.py`
- Email log script: `scripts/log_sent_email.py`

## Google Workspace config

The skill uses the Neon Blonde Google Workspace config at:

`/Users/studio_hub/Google Workspace Configs/Neon Blonde`

It also expects the Hermes token at:

`/Users/studio_hub/.hermes/google_token.json`

## GroupMe sync

GroupMe exports are read from:

`/Volumes/Drive_A/GroupMeChats/messages`

If the drive is not mounted, the workflow reports that explicitly and asks the user to mount Drive A.

## Notes

- The repo is designed for local terminal workflows.
- It includes a CLI-Anything-based GIMP harness for venue template projects.
- The skill content still refers to the real band name, Neon Blonde, where appropriate.
