# Neon V2

Neon V2 is the booking and rehearsal operations skill for Neon Blonde.

It handles:
- calendar availability checks with strict sanity rules
- rehearsal-date shortlists and rehearsal reservation emails
- venue package creation for confirmed gigs
- GroupMe message sync and communication logging
- plain-language Band Sheet generation
- venue research and booking follow-up
- AgentMail and Telegram communication

## Key Paths

- Skill file: `SKILL.md`
- Booking workflow: `references/booking-workflow.md`
- Availability rules: `references/availability-verification.md`
- Band Sheet format: `references/band-sheet-format.md`
- Band Sheet JSON usage: `references/bandsheet-data-json.md`
- Briefing cross-reference workflow: `references/briefing-cross-reference.md`
- Rehearsal email template: `references/rehearsal-email-template.md`
- AgentMail protocol: `references/agentmail-protocol.md`
- Phillip Thomas protocol: `references/phillip-thomas-protocol.md`
- Venue package script: `scripts/create_venue_package.sh`
- Rehearsal shortlist script: `scripts/find_rehearsal_dates.py`
- GroupMe sync script: `scripts/sync_groupme_messages.py`
- Calendar fetch script: `scripts/fetch_calendar_with_ranges.py`
- Email log script: `scripts/log_sent_email.py`

## Identity

The active assistant name is **Neon V2**.

There is no fictional character file in the live skill. Keep responses direct, plain-language, and operational.

## Google Workspace Config

The skill uses the Neon Blonde Google Workspace config at:

`/Users/studio_hub/Google Workspace Configs/Neon Blonde`

It also expects the Hermes OAuth token at:

`/Users/studio_hub/.hermes/neon_oauth_token.json`

Legacy helper scripts may still reference:

`/Users/studio_hub/.hermes/google_token.json`

If a helper script fails because it expects the legacy token, report the exact token path mismatch instead of guessing.

## GroupMe Sync

GroupMe exports are read from:

`/Volumes/Drive_A/GroupMeChats/messages`

If the drive is not mounted, report that explicitly and ask Mike to mount Drive A.
