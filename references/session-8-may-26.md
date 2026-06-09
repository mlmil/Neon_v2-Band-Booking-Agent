# Session 8: May 26, 2026 — Quick Pulse Check (Cron-Fired)

> Superseded status note (Jun 9, 2026): the Jeff wedding contract is no longer stalled at the May 19 re-attachment request. Current Gmail/Drive evidence is tracked in `references/venues.md`; use that active reference for future briefings.

## Setup

- **Date**: Tuesday, May 26, 2026
- **Type**: Quick pulse check (cron-fired, no user present)
- **Band Sheet**: Updated May 25, 2026 @ 9:23 AM PT — **1 day fresh** (first fresh Band Sheet in all documented sessions)
- **Pending approvals**: Empty session log only (clean — no false positives this run)
- **Monitor script**: Returned 0 events (standard cron OAuth hang — expected)
- **OAuth token**: `invalid_grant: Token has been expired or revoked.` — **fully dead**, not just stale client_secret. This is a different error from `invalid_client` (documented in existing pitfalls) and the first time inline OAuth has failed entirely.

## What Changed vs Prior Sessions

Band Sheet was **fresh** for the first time in the worked-example history (prior sessions ranged 9–13 days stale). This changed the compounding assessment baseline: listings started with 0 negatives from freshness instead of 1.

## Data Sources That Worked

| Source | Status | Notes |
|--------|--------|-------|
| Band Sheet JSON endpoint | ✅ Fresh (May 25) | `bandsheet-data.json` returned full data with `updated` field |
| Calendar inline OAuth | ❌ Failed | `invalid_grant` — token cannot refresh. VADER drive not mounted. |
| Freshground iCal feed | ✅ Worked | Found 8 events in next 2 weeks, including 2 Neon Blond rehearsals |
| Email IMAP (per-contact) | ✅ Worked | Found messages from 3 contacts, latest from May 15 |
| Sent mail IMAP | ✅ Worked | Confirmed venue change, rehearsal request, stalled contract |
| Venue folders (Drive sync) | ✅ Worked | All 4 upcoming gigs had folders |

## What We Knew Without the Calendar

Without calendar access, we relied on:
- **Band Sheet** for confirmed gigs (dates, times, venues, member-outs)
- **Email** for booking context and stalled threads
- **Sent mail** for venue confirmations and rehearsal origin
- **Venue folders** on Drive for package existence checks
- **Freshground iCal feed** for rehearsals

The Band Sheet was fresh enough to be the primary source of truth. The missing calendar data meant we couldn't:
- Check for tentative gigs not on the Band Sheet
- Verify member-out events beyond what the Band Sheet lists
- View event creator fields for authority checks

## Freshground Calendar Findings

Two Neon Blond rehearsals found (both on Tuesdays, 7–10pm Pacific):
| Date | Event | Notes |
|------|-------|-------|
| Tue May 26 | `- 10 Neon Blond` | TONIGHT at 7pm — no sent mail trail for this date |
| Tue Jun 2 | `- 10 Neon Blnd` | Also 7–10pm — also no sent mail trail |

The sent mail to Freshground contained only one rehearsal request (Thu May 21, sent May 18). Neither the May 26 nor Jun 2 rehearsals have matching sent mail — they may be a standing Tuesday arrangement. This confirms: **after finding the first rehearsal in sent mail, scan for ALL upcoming Neon Blond events on Mark's calendar, not just the one you searched for.**

Also on May 26 at Freshground: `- 6 P & P` at 4pm (another band rehearsing before Neon Blond).

## Email Sweep Results

| Contact | Last Message | Status |
|---------|-------------|--------|
| Jeff (jefftl123) | May 15 (signed contract) | **Stalled** — Mike asked for re-attachment May 19, no reply. |
| Phillip Thomas (rockstar) | May 11 (Festivals) | Resolved. Sent thumbs-up. No follow-up from Phillip. |
| thebikeguyiv (Phillip) | May 11 (Dates list) | Info only. No new messages since. |
| Sin Chonies (Alfred) | — | No booking-related emails found. |
| Dave (dukes) | — | No messages in search window. |

**UNSEEN safety net**: 0 unseen messages outside known contacts. Booking pipeline quiet since May 15.

## Sent Mail Resolution

| Search | Result |
|--------|--------|
| `SUBJECT "Harry"` SINCE 10-May | ✅ Found: "Updated Bandsheet Graphics — Harry's Nightclub" (May 19, to Alfred). Confirms Leashless→Harry's change. |
| `SUBJECT "Tony"` SINCE 10-May | ❌ No results. Tony's Pizza bookings have no email confirmation trail. |
| `SUBJECT "Figueroa"` | ❌ No results. Booking handled outside email. |
| `TO freshgroundrecords` SINCE 1-May SUBJECT "rehearsal" | 1 message: May 21 request (sent May 18). The May 26 and Jun 2 rehearsals have no sent mail trail — possibly a standing arrangement. |

## Venue Folders (Next 14 Days)

| Gig | Folder | Notes |
|-----|--------|-------|
| Wed 5/27 Santa Barbara Yacht Club | ✅ `Santa Barbara Yacht Club - 5 27 2026` | |
| Fri 5/29 Figueroa Mountain | ✅ `Figueroa Mountain - 5 29 2026` | |
| Fri 6/5 Harry's Night Club | ✅ `Harry's Night Club & Beach Bar - 6 5 2026` | Also stale folder: `Leashless - 6 5 2026` |
| Sat 6/6 Tony's Pizza | ✅ `Tony's Pizza - 6 6 2026` | |

**Rogue folder detected**: `Kyle Out - 7 3 2026` — member-out event folder in Venues directory. Flagged in briefing.

## Compounding Assessment (Fresh Band Sheet = 0 negatives from freshness)

| Gig | Negatives | Overlap? | Verdict |
|-----|-----------|----------|---------|
| Wed 5/27 SB Yacht Club | 1 (not on Band Sheet) | No | Advisory — calendar-only gig not yet on site |
| Fri 5/29 Figueroa Mountain | 0 | No | **Fully solid** — fresh Band Sheet + folder |
| Fri 6/5 Harry's Night Club | 0 | No | Solid — fresh Band Sheet has the updated name |
| Sat 6/6 Tony's Pizza | 0 | No | Solid — fresh Band Sheet + folder + no conflicts |

## ⚠️ OAuth: `invalid_grant` vs `invalid_client` — New Error Mode

Previous sessions had inline OAuth working with cached token auto-refresh. This session hit `invalid_grant: Token has been expired or revoked.` — distinct from `invalid_client` (client secret rotated, documented in existing pitfalls).

**Diagnosis**:
- `invalid_client` = Google Cloud project's client secret was rotated. **Fix**: edit the token file's `client_secret` field with the new value from VADER drive.
- `invalid_grant` = The actual refresh token is invalid/revoked. **Fix**: Full browser re-auth needed via `scripts/generate_oob_auth_url.py`. Editing the token file won't help.

**Fallback**: When OAuth is broken AND VADER isn't mounted, the Band Sheet (if fresh) + email + sent mail + venue folders provide a complete enough picture for briefings. The worked example's "what you can't do" list still applies.

## Key Takeaway for Future Sessions

1. **Fresh Band Sheet changes the baseline**: When the sheet is ≤4 days old, do NOT add 1 negative to every listing. The compounding assessment starts from 0. A fresh sheet also means the site is being actively maintained — trust its listings more than when it's stale.

2. **OAuth can die between sessions**: The token that worked for 7 consecutive sessions can fail on the 8th. Always be prepared for the Band Sheet fallback. Do not assume that if it worked last time, it will work this time.

3. **Two rehearsals found when searching broadly**: Always scan ALL Freshground events for "Neon" after finding the first one. Standing arrangements produce multiple dates that won't match a specific sent mail request.

4. **Email silence is useful context**: No new booking emails since May 15 means the pipeline is quiet. Report this status in the briefing — it means no news is good news.
