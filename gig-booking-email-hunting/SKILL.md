---
name: gig-booking-email-hunting
description: Find the emails that booked a specific Neon Blonde gig, pin the exact gig date before searching, and resolve (or honestly report missing) private-party street addresses.
---

# Gig Booking Email Hunting

Use whenever Mike asks to "find the emails that booked" a gig, "hunt down" a booking thread, or get details (address, time, pay) for an upcoming show from email.

## Core rules

1. **Pin the exact gig date FIRST.** "This Saturday" is ambiguous — multiple "this Saturday" threads exist at any time (e.g., a July 29 email about Fig Mountain booked Aug 1, a past gig, while the Aug 8 party was booked by a different thread). Compute the next occurrence from today, then confirm venue/city/time against the live Band Sheet (`https://mlmil.github.io/NeonBlonde-Bandsheet/docs/`, BOOKED GIGS section) before searching.
2. **Do not grab the most recent email mentioning "Saturday."** Match on the gig date, not the word.
3. **Search the full thread, not just recent messages.** A booking thread spans the original inquiry through the latest logistics reply.

## Search recipe

Run from `/Users/cthulhu/Desktop/Skill FIles/Neon_v2` (read-only, never marks messages read):

1. First pass: `python3 scripts/list_recent_emails.py --limit 50` — note the newest `--limit` is 50; for deeper scans use the fetch_recent/IMAP helpers directly (see below).
2. Find the sender: check `references/band-members.md` (booking contacts table) and the Band Sheet gig entry for likely names.
3. Pull the full thread across **INBOX + "[Gmail]/Sent Mail" + "[Gmail]/All Mail"** with `BODY.PEEK[]` so quoted replies and sent confirmations are included. Filter by sender domain (e.g., `mory@822group.com`) plus subject terms matching the event (e.g., "Summer Party in SB Aug 8th").
4. Search bodies for date patterns (`Aug 8`, `8/8`, `August 8`) and the venue name. Watch for `Automatic reply:`/`Security alert` noise — skip it.

## Private-party addresses

A street address is often **NOT in the email thread**. Clients typically only say the city ("We're in Santa Barbara", "backyard by the pool"). Check in order:

1. Full thread bodies (INBOX + Sent + All Mail) for street-number + street-suffix patterns and CA zips.
2. Venue folder under `$NEON_DRIVE_ROOT/Venues/` (naming: `Venue - M D YYYY`). Private parties may have no folder.
3. `Neon Blonde Booking Contacts.md` and any venue notes files.
4. Google Contacts: `python3 scripts/google_contacts_tool.py search "<name>"` (needs `google-auth` + `google-api-python-client` installed; run `pip3 install google-auth google-auth-oauthlib google-api-python-client` if missing).

**If no address exists anywhere: tell Mike plainly you cannot find it. NEVER fabricate an address.** Mike explicitly requires this honesty ("if you can't find it, tell me you can't find it"). Do not send members a made-up address — ask Mike for it (he often has it from a previous year's booking or a text).

## Pitfalls

- IMAP `SEARCH` fails on multi-word FROM terms like `'FROM', 'Mory Fontanez'` — use the email address only (`'FROM', 'mory@822group.com'`).
- `list_recent_emails.py --limit` is capped at 50; for more, call its `fetch_recent()` directly or iterate IMAP UIDs.
- Google Contacts tool fails with `ModuleNotFoundError` until `google-api-python-client` is installed; that is a setup fix, not a reason to skip the check.
- The address for a repeat party may only exist in Mike's phone/texts — asking him is the correct step, not guessing.
