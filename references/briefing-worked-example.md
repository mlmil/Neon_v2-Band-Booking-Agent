# Briefing Workflow — Worked Example (May 21-23, 2026)

> Superseded status note (Jun 9, 2026): Jeff's Wedding contract references in this worked example describe the May stalled state only. For current handling, use `references/venues.md` and `scripts/contract_flow.py`.

## Purpose

This document shows how the full briefing workflow (Phases 1–4 in SKILL.md) fits together as a single end-to-end process. It's a concrete reference for future sessions: what data to fetch, in what order, how to cross-reference, and how to synthesize.

---

## Session 1: May 21, 2026

## Phase 0: Setup

**Today's date**: Thursday, May 21, 2026  
**Band Sheet updated**: May 12, 2026 (9 days stale)  
**Pending approvals**: Empty

---

## Phase 1 — Calendar Data

### Step 1A: Run the monitor script (fast scan)

```bash
python3 ~/.hermes/scripts/neon_monitor.py
```

**⚠️ May silently return 0 events** in cron/automation. When that happens, proceed with inline OAuth — don't abort.

### Step 1B: Inline OAuth for detailed events

When the monitor script returns 0, use the Google API client directly:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ⚠️ No scopes param — the token file embeds its own scopes.
creds = Credentials.from_authorized_user_file(
    str(Path.home() / '.hermes' / 'neon_oauth_token.json')
)
service = build('calendar', 'v3', credentials=creds)

today = date.today()
time_min = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).isoformat()
time_max = (datetime.combine(today + timedelta(days=60), datetime.min.time(), tzinfo=timezone.utc)).isoformat()

events_result = service.events().list(
    calendarId='neonblondevc@gmail.com',
    timeMin=time_min, timeMax=time_max,
    singleEvents=True, orderBy='startTime',
    fields='items(summary,start,end,location,description,creator)',
    maxResults=250,
).execute()
```

**Always include** `location`, `description`, and `creator` in fields. Location resolves venue city ambiguity. Description may have booking notes. Creator tells you if Mike or a band member created the event.

### Step 1C: Freshground calendar (rehearsals)

Fetch the iCal feed and filter by year:

```python
import urllib.request, re
from datetime import datetime, timezone, timedelta

pacific = timezone(timedelta(hours=-7))
resp = urllib.request.urlopen(
    "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics",
    timeout=15
)
ics = resp.read().decode('utf-8')
events = re.split(r'BEGIN:VEVENT', ics)
for ev in events:
    if 'DTSTART:2026' in ev and 'Neon' in ev:
        # parse and report
```

**⚠️ The feed has ~2900 VEVENTs**. Always filter by year.

### Step 1D: Fetch the Band Sheet website

```python
from hermes_tools import web_extract
result = web_extract(urls=["https://mlmil.github.io/NeonBlonde-Bandsheet/docs/"])
```

**Check the freshness date immediately.** When using the JSON endpoint (`bandsheet-data.json`), check the `updated` field — it's equivalent to the website footer date but available without rendering the React site. A freshness signal >4 days old means the site is stale — treat all listings with elevated suspicion.

---

## Phase 2 — Email Sweep

### Step 2A: Per-contact IMAP sweep

```python
import imaplib, json
from pathlib import Path

with open(str(Path.home() / '.hermes' / 'skills' / 'Neon_v2' / 'smtp_config.json')) as f:
    cfg = json.load(f)

mail = imaplib.IMAP4_SSL(cfg['imap_host'], cfg['imap_port'])
mail.login(cfg['email'], cfg['app_password'])
mail.select('INBOX')

contacts = ['rockstarentertainment805', 'jefftl123', 'dave@dukesbeachgrill', 'thebikeguyiv', 'sin.chonies.inc']
all_ids = set()
for addr in contacts:
    status, data = mail.search(None, f'(FROM "{addr}" SINCE "7-May-2026")')
    if status == 'OK' and data[0]:
        all_ids.update(data[0].split())
```

### Step 2B: Read latest message bodies

```python
s_h, hdr = mail.fetch(latest_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
s_b, body = mail.fetch(latest_id, '(BODY.PEEK[TEXT])')
```

### Step 2C: UNSEEN safety net

```python
status, data = mail.search(None, '(UNSEEN)')
if status == 'OK' and data[0]:
    unseen_ids = set(data[0].split())
    new_ids = unseen_ids - all_ids
```

### Step 2D: Sent Mail search

When venue name mismatch occurs, check sent mail. Use `(RFC822)` fetch + `email.message_from_bytes()`:

```python
import email
from email import policy
mail.select('"[Gmail]/Sent Mail"')
for keyword in ['Harry', 'Leashless']:
    status, data = mail.search(None, f'(SUBJECT "{keyword}" SINCE "7-May-2026")')
    if status == 'OK' and data[0]:
        msg_id = data[0].split()[-1]
        s_full, raw = mail.fetch(msg_id, '(RFC822)')
        if s_full == 'OK':
            msg = email.message_from_bytes(raw[0][1], policy=policy.default)
```

**⚠️ Sent Mail folder requires explicit quoting**: `'"[Gmail]/Sent Mail"'`

---

## Phase 3 — Stale Drafts

```python
with open(str(Path.home() / '.hermes' / 'neon_pending_approvals.json')) as f:
    drafts = json.load(f)
```

Auto-discard false positives. Flag ambiguous entries in briefing.

---

## Phase 4 — Cross-Reference & Compounding Signal Assessment

### Worked Example — May 21, 2026

#### Figueroa Mountain (Fri May 29, 6pm)

| Signal | Result |
|---|---|
| Freshness | ❌ Site stale |
| Calendar match | ✅ Event exists, 6-9pm, location: Santa Barbara |
| Venue folder | ✅ Figueroa Mountain - 5 29 2026 exists |
| Tentative member-out | ✅ All clear |

**Assessment**: 1 negative (stale site). Solid.

#### Tony's Pizza (Sat May 30, 7pm) — Multi-signal failure

| Signal | Result |
|---|---|
| Freshness | ❌ Site stale |
| Calendar match | ❌ No event on May 30 |
| Venue folder | ❌ No folder for this date |
| Email cross-ref | ❌ Bike Guy says "5/31 tentative" — date/status mismatch |
| Tentative member-out | ❌ Kyle Out (probably) overlaps |

**Assessment**: 4 negatives + tentative overlap = Highest priority.

#### Santa Barbara Yacht Club (Wed May 27) — Calendar-only gig

Not on Band Sheet. On calendar (Mike-created). Venue folder exists. Assessment: site lagging.

#### June 5 — Leashless (Band Sheet) vs Harry's (Calendar) — Venue name mismatch

Sent mail confirms Harry's. Both folders exist on Drive. Band Sheet graphics updated May 19.

---

## Session 2: May 22, 2026

### Setup
- **Date**: Friday, May 22, 2026
- **Band Sheet**: May 12 (10 days stale)
- **Pending approvals**: 1 false positive (discarded)

### Calendar Findings (inline OAuth, 60-day window)

17 events found. Next 2 weeks:

| Date | Event | Creator |
|---|---|---|
| May 23-24 | Alfred Out | neonblondevc@gmail.com |
| May 23-26 | Curtis Out | neonblondevc@gmail.com |
| Wed May 27, 6-8:30pm | Santa Barbara Yacht Club | neonblondevc@gmail.com |
| Fri May 29, 6-9pm | Figueroa Mountain (SB) | neonblondevc@gmail.com |
| May 30-31 | Kyle Out (probably) | kyle.fegley@gmail.com |
| Fri Jun 5, 9pm-midnight | Harry's Night Club (Pismo) | neonblondevc@gmail.com |
| Sat Jun 6, 7pm-midnight | Tony's Pizza (Ventura) | neonblondevc@gmail.com |
| Fri Jun 12, 9-11pm | Cruisery (SB) | 4lfred20@gmail.com |
| Sat Jun 13, 3-4pm | Fess Parker Winery | neonblondevc@gmail.com |

### Freshground Calendar

| Date | Event | Time (Pacific) |
|---|---|---|
| Thu May 21 | - 10 Neon Blond | 7-10pm (past) |
| Tue May 26 | - 10 Neon Blond | 7-10pm (upcoming) |

Note: May 26 rehearsal wasn't the subject of any recent sent mail — it may be a standing arrangement. Per the skill, scan for additional rehearsals proactively.

### Email Sweep Results

| Contact | Date | Status |
|---|---|---|
| Phillip Thomas (rockstar) | May 11 "Festivals" | Resolved — Mike said yes |
| Jeff (jefftl123) | May 12-15 "Wedding Contract" | **Stalled** — Jeff signed, Mike asked for re-attach on May 19 |
| thebikeguyiv | May 11 "Dates from..." | Info: Fig Mtn 7-10pm, Tony's 5/31 tentative, Tony's 6/6 7-10, Fox Wine 4-7 |
| Alfred (sin.chonies) | May 8 daily check | False positive (automated) |

### Sent Mail Resolution

- **Harry's / Leashless**: Mike sent "Updated Bandsheet Graphics — Harry's Nightclub" to Alfred on May 19. Confirms venue change.
- **Rehearsal**: Mike requested May 21 from Mark on May 18. Matches Freshground calendar.
- **Wedding contract**: Mike replied to Jeff on May 19 asking for doc re-attachment. No reply yet.

### Cross-Reference Highlights

#### Santa Barbara Yacht Club (May 27)
- ❌ Not on Band Sheet (stale), ✅ Calendar, ✅ Venue folder, ✅ No member conflicts
- **1 negative** — advisory

#### Figueroa Mountain (May 29) — Email time mismatch
- Calendar: 6-9pm. Bike Guy email: 7-10pm. Band Sheet: @6pm. Calendar matches Band Sheet.
- **Resolution**: The email time (7-10) likely reflects an initial proposal that was adjusted to 6-9. Flag as advisory discrepancy.
- **Assessment**: 1 negative (stale site) + 1 advisory (time mismatch). Solid.

#### Tony's Pizza (May 30) — Multi-signal failure
- ❌ Site stale, ❌ No calendar event, ❌ No venue folder, ❌ Bike Guy says 5/31 tentative, ❌ Kyle Out probably overlaps
- **4 negatives + tentative overlap = HIGHEST PRIORITY**

#### Cruisery (Jun 12) — Band member creator
- Creator: 4lfred20@gmail.com (Alfred). Per band member creator rule, treated as confirmed. No need to flag as uncertain.
- **1 negative** (stale site). Solid.

### Key Cross-Session Patterns

1. **Band Sheet freshness can flip** — The first 7 sessions (May 21–25) had the Band Sheet 9–13 days stale. Session 8 (May 26) found it 1 day fresh. Do not assume persistent staleness — check the `updated` field every time. A fresh sheet changes the baseline from "every listing starts with 1 negative" to "listings start with 0 negatives."

See `references/session-8-may-26.md` for the first documented case of a fresh Band Sheet and the compounding assessment under zero-staleness conditions.

2. **Scan Freshground for ALL upcoming Neon Blond rehearsals** — After finding the first rehearsal matching a sent mail request, do a wider scan for ALL "Neon" events on Mark's calendar. Standing arrangements produce dates without email trails. Both May 26 and Jun 2 rehearsals were found in Session 8; reporting them together (not as separate discoveries) is expected.

3. **`invalid_grant` = hard OAuth death** — When the token returns `invalid_grant` (vs `invalid_client`), auto-refresh is not recoverable by editing the token file. Requires full browser re-auth via `generate_oob_auth_url.py`. The Band Sheet fallback (if fresh) + email + sent mail + venue folders covers most briefing needs without calendar data.
2. **Email time mismatches** are common with Phillip/Bike Guy (proposed vs actual). Flag but don't treat as conflicts unless calendar was created by a non-band member.
3. **Band member-created events** (Alfred on Cruisery, Kyle on Kyle Out) are trustworthy. Distinguished from external-created events.
4. **"Both folders exist" on Drive** = strong signal of a venue change. Confirm via sent mail.
5. **calendar-notification@google.com false positives** happen every monitor run. Auto-discard immediately — don't leave in pending.
6. **Sent mail search** resolves venue name mismatches faster than asking Mike. Always check first.

---

## Session 3: May 23, 2026

### Setup
- **Date**: Saturday, May 23, 2026
- **Band Sheet**: May 12 (11 days stale)
- **Monitor script**: Returned 0 events (OAuth blocks in cron — expected. Proceeded with inline OAuth.)
- **Pending approvals**: 1 false positive (Google Calendar notification — discarded immediately per Phase 3 pattern)

### Calendar Findings (inline OAuth, 60-day window, creator field included)

Events in the next 2 weeks (filtered from 17 total):

| Date | Event | Creator | Notes |
|---|---|---|---|
| May 23 | Alfred Out | Mike | Single day |
| May 23-26 | Curtis Out | Mike | Multi-day, spans 4 days |
| Wed May 27, 6-8:30pm | Santa Barbara Yacht Club | Mike | Location: Santa Barbara |
| Fri May 29, 6-9pm | Figueroa Mountain (SB) | Mike | Location: Santa Barbara |
| May 30-31 | Kyle Out (probably) | kyle.fegley@gmail.com | Tentative, across weekend |
| Fri Jun 5, 9pm-midnight | Harry's Night Club (Pismo) | Mike | Confirmed via sent mail |
| Sat Jun 6, 7pm-midnight | Tony's Pizza (Ventura) | Mike | Location: Ventura |
| Fri Jun 12, 9-11pm | Cruisery (SB) | 4lfred20@gmail.com | Alfred-created, trusted |
| Sat Jun 13, 3-4pm | Fess Parker Winery | Mike | Short afternoon slot |

### Band Sheet Cross-Reference

Band Sheet lists these confirmed gigs (all from May 12):

| Band Sheet Listing | Calendar Match? | Verdict |
|---|---|---|
| Fri May 29 Fig Mtn @ 6pm | ✅ Yes, 6-9pm | Match. Fig Mtn drives 6-9 |
| Sat May 30 Tony's @ 7pm | ❌ No event | Missing from calendar |
| Wed Jun 3 Tony's @ 7pm | ✅ Yes, Tony's 7-12 | Match |
| Fri Jun 5 Leashless @ 9pm | ⚠️ Harry's instead | Venue changed (sent mail) |
| Sat Jun 6 Tony's @ 7pm | ✅ Yes, 7-midnight | Match |
| Fri Jun 12 Cruisery @ 9pm | ✅ Yes, 9-11pm | Match |
| Sat Jun 13 Fess Parker @ 3pm | ✅ Yes, 3-4pm | Match |

### Email Sweep Results

| Contact | Latest Email | Status |
|---|---|---|
| Phillip Thomas (rockstar) | May 11 | No new messages since |
| Jeff (jefftl123) | May 15 contract | Still stalled — Jeff hasn't replied to Mike's May 19 request |
| thebikeguyiv (Phillip) | May 11 | No new messages since |
| freshgroundrecords | Rehearsal request May 18 | Mark added rehearsal to his calendar (May 21 + May 26) |

**Unseen emails**: 0 new unseen messages beyond known contacts. No booking noise detected.

### Freshground Calendar (Rehearsals)

- **Tue May 26**: `- 10 Neon Blond` (7-10pm Pacific) — already confirmed, no action needed
- **No other Neon Blond rehearsals** in the next 30 days

### Sent Mail Check Results

- **"Tony" search**: No sent emails found — no confirmation thread for the Tony's Pizza 5/30 date mismatch
- **"Figueroa" search**: No sent emails — the Fig Mtn booking appears to have been handled outside email (possibly GroupMe or direct word)
- **Freshground check (rehearsal)**: Sent mail confirmed the May 21 rehearsal request was sent on May 18. Mark's calendar now shows BOTH May 21 and May 26 — the May 26 date was likely booked separately or as a standing arrangement. No follow-up sent email needed.

### Compounding Signal Assessment

**Figueroa Mountain (Fri May 29, 6pm)** — Updated with time-mismatch resolution:
- ❌ Site stale (1 negative)
- ✅ Calendar event (Mike-created, 6-9pm matches Band Sheet's @6pm)
- ✅ Venue folder exists
- ✅ No member conflicts (Curtis out ends May 26, Alfred out May 23 only)
- ⚠️ Email time mismatch resolved: Bike Guy said 7-10pm, but calendar creator = Mike, so calendar time (6-9pm) is authoritative. Emailed time was a proposal.
- **Assessment**: 1 negative, resolved advisory. Solid.

**Tony's Pizza (Sat May 30)** — Still unresolved:
- ❌ Site stale
- ❌ No calendar event for May 30 (calendar has Tony's on Jun 6 only)
- ❌ No venue folder for 5/30 (Tony's Pizza - 6 6 2026 folder exists for June 6, but NOT for May 30)
- ❌ Bike Guy says 5/31 tentative (different date entirely)
- ❌ Kyle Out probably overlaps
- **Assessment**: 4 negatives + tentative overlap. HIGHEST PRIORITY. No sent mail trail to break the tie. Needs Mike to confirm whether this date is real and which day.

**Santa Barbara Yacht Club (Wed May 27)** — Calendar-only, not on Band Sheet:
- ❌ Not on Band Sheet (stale site must have missed it)
- ✅ Calendar event (Mike-created, 6-8:30pm)
- ✅ Venue folder exists
- ✅ No member conflicts this week
- **Assessment**: 1 negative. Solid — site just hasn't been updated.

**Cruisery (Fri Jun 12, 9pm)** — Alfred-created:
- ❌ Site stale
- ✅ Calendar (Alfred created — trusted per band member rule)
- No venue folder check needed (Alfred likely handles his own setup)
- ✅ No member conflicts on calendar
- **Assessment**: 1 negative. Solid.

### False-Positive Handling

- **Google Calendar notification** (calendar-notification@google.com): The monitor script's keyword-based flagging caught it as a "booking" — IMMEDIATELY discarded per Phase 3 rule. Cleared from pending_approvals.json.

### Key Patterns Observed in This Session

1. **Monitor script returned 0 events in cron context** — as documented in the OAuth pitfall. The inline OAuth fallback worked immediately. This will happen every time in automated/routine sessions; don't bother re-running the script.

2. **Email time discrepancy + creator-based resolution**: The Bike Guy's Fig Mtn time (7-10pm) differed from the calendar (6-9pm). Since Mike created the calendar event, the calendar time is authoritative. The email was an initial proposal. This is now a documented resolution path in the skill.

3. **Date mismatch + no sent mail trail**: Tony's Pizza 5/30 has no supporting evidence from any source — no calendar event, no sent mail, no venue folder, and the Bike Guy's tentative 5/31 conflicts. This is the hardest class of ambiguity. The compounding signal assessment correctly flags it as highest priority. Without a calendar event OR sent mail, it stays uncertain until Mike decides.

4. **Negative sent mail searches are useful**: Searching for "Tony" in sent mail and finding nothing is itself a meaningful signal — it means there's no paper trail to fall back on, elevating the uncertainty level. Add negative results to the briefing as supporting evidence.

5. **Alfred-created gig (Cruisery)**: A reminder that band member-created events on the calendar are trusted without extra verification. No need to flag them as uncertain — the creator field check resolves it.

6. **Regular checking of pending_approvals.json**: Every session should clear this file. false positives accumulate across sessions. The calendar-notification pattern happened on this session's run, meaning it's a recurring (possibly daily) false-positive source.

7. **`invalid_grant` vs `invalid_client` — Two OAuth failure modes**: Sessions 1–7 had working inline OAuth via auto-refresh. Session 8 hit `invalid_grant: Token has been expired or revoked.` — a hard token death. Distinguish from `invalid_client` (client secret rotated, fixable by editing token file) — `invalid_grant` requires full browser re-auth via `generate_oob_auth_url.py`. See `references/session-8-may-26.md` for the first documented `invalid_grant` case.

---

## Session 4: May 23, 2026

### Setup
- **Date**: Saturday, May 23, 2026
- **Band Sheet "Updated:" footer**: May 12, 2026 — **11 days stale** (flags every listing with at minimum 1 negative signal before any other check)
- **Pending approvals file**: Empty (no lingering drafts from prior cycles)
- **Monitor script**: Returned 0 events (standard cron OAuth hang — proceeded with inline OAuth per established pattern)

### Calendar Findings

Inline OAuth fetch (60-day window, creator field included):

| Date | Event | Creator | Notes |
|---|---|---|---|
| May 23 (Sat) | Alfred Out | neonblondevc@gmail.com | Single-day all-day event |
| May 23-26 (Sat-Tue) | Curtis Out | neonblondevc@gmail.com | Multi-day, ends Tue May 26 |
| Wed May 27, 6-8:30pm | Santa Barbara Yacht Club | neonblondevc@gmail.com | Midweek, Mike-created, not on Band Sheet |
| Fri May 29, 6-9pm | Figueroa Mountain (SB) | neonblondevc@gmail.com | Location: Santa Barbara |
| May 30-31 (Sat-Sun) | Kyle Out (probably) | kyle.fegley@gmail.com | Tentative, across full weekend |
| Wed Jun 3, 7pm-midnight | *(no calendar event exists)* | — | Band Sheet says Tony's @ 7pm |
| Fri Jun 5, 9pm-midnight | Harry's Night Club (Pismo) | neonblondevc@gmail.com | Band Sheet still says Leashless |
| Sat Jun 6, 7pm-midnight | Tony's Pizza (Ventura) | neonblondevc@gmail.com | Location: Ventura |
| Fri Jun 12, 9-11pm | Cruisery (SB) | 4lfred20@gmail.com | Alfred-created (trusted) |
| Sat Jun 13, 3-4pm | Fess Parker Winery | neonblondevc@gmail.com | Short afternoon slot |

### Band Sheet Cross-Reference

| Band Sheet Listing | Calendar Match? | Verdict |
|---|---|---|
| Fri May 29 Fig Mtn @ 6pm | ✅ Yes, 6-9pm | Solid. Calendar time (6-9) matches |
| Sat May 30 Tony's @ 7pm | ❌ No event | Missing entirely. No venue folder. | 
| Wed Jun 3 Tony's @ 7pm | ❌ No event | Missing. Weekday (Wed) = unusual |
| Fri Jun 5 Leashless @ 9pm | ⚠️ Harry's instead | Venue change confirmed via sent mail |
| Sat Jun 6 Tony's @ 7pm | ✅ Yes, 7-midnight | Match. Venue folder exists |
| Fri Jun 12 Cruisery @ 9pm | ✅ Yes, 9-11pm | Match. Alfred-created |
| Sat Jun 13 Fess Parker @ 3pm | ✅ Yes, 3-4pm | Match |

### ⚠️ Key Discovery: Tony's Pizza — Multiple-Date Venue Gap

Tony's Pizza is listed on the Band Sheet for THREE dates: May 30, Jun 3, and Jun 6. But only **Jun 6** has a calendar event. This is the first instance of a **systematic staleness pattern**: 2/3 of a venue's dates are missing from the calendar simultaneously.

| Date | Calendar | Venue Folder | Email Cross-ref | Tag |
|---|---|---|---|---|
| Sat May 30 | ❌ | ❌ | Bike Guy says "5/31 tentative" — different date | 4 negatives + Kyle Out overlap = HIGHEST |
| Wed Jun 3 | ❌ | Not checked (no event) | No email reference | 2 negatives + weekday flag |
| Sat Jun 6 | ✅ Yes, 7-midnight | ✅ Tony's Pizza - 6 6 2026 | Bike Guy says 6/6 7-10pm (close match) | 1 negative (stale site only) |

This suggests the Band Sheet's Tony's listings were bulk-entered from a proposal that only partially materialized. The Jun 6 date is solid (calendar + folder + email + no member conflicts). The other two dates lack supporting evidence from every source.

### Email Sweep Results

| Contact | Latest | Status |
|---|---|---|
| thebikeguyiv (Phillip) | May 11: Fig Mtn 7-10, Tony's 5/31 tentative, Tony's 6/6 7-10, Fox Wine 4-7 | No new messages since |
| Jeff (jefftl123) | May 15: Signed wedding contract | **Stalled** — Mike asked for re-attachment May 19, no reply |
| David Child (dukes) | — | No messages in search window |
| Phillip Thomas (rockstar) | May 11: Festival inquiries | Resolved — Mike said yes |
| Alfred (sin.chonies) | — | No booking-related emails |

**UNSEEN check**: 0 new unseen messages outside known contacts. No noise.

### Sent Mail Search Results

| Search Term | Result |
|---|---|
| `TONY` or `Tony's` | **Nothing found** — no sent mail confirms either the May 30 or Jun 3 date. This is a meaningful negative signal: the venue booking happened outside email (likely GroupMe or phone) or the dates were never confirmed. |
| `Figueroa` | **Nothing found** — booking may have been handled outside email too. |
| `Freshground` / Mark | May 18 rehearsal request found. Confirms Mark added May 21. No sent mail found for the May 26 rehearsal — that date was arranged separately. |
| `Harry` | Found — May 19 "Updated Bandsheet Graphics" confirming venue change from Leashless. |

### Freshground Calendar (Rehearsals)

| Date | Event | Time (Pacific) | Notes |
|---|---|---|---|
| Tue May 26 | - 10 Neon Blond | 7-10pm | No sent mail trail — possibly a standing weekly arrangement |
| No other Neon Blond rehearsals in next 30 days | | | |

### Compounding Assessment (per-skif.l Phase 4, Step 13)

**Santa Barbara Yacht Club (Wed May 27)**
- ❌ Site stale (1)
- ✅ Calendar (Mike-created, 6-8:30pm)
- ✅ Venue folder exists
- ✅ No member conflicts (Curtis out ends May 26)
- **1 negative — advisory. Solid.**

**Figueroa Mountain (Fri May 29)**
- ❌ Site stale (1)
- ✅ Calendar (Mike-created, 6-9pm)
- ✅ Venue folder exists
- ✅ No member conflicts
- ⚠️ Email time mismatch (Bike Guy said 7-10pm, calendar says 6-9pm) — resolved via creator authority
- **1 negative — solid.**

**Tony's Pizza (Sat May 30)**
- ❌ Site stale (1)
- ❌ No calendar event (1)
- ❌ No venue folder (1)
- ❌ Email cross-ref says 5/31 not 5/30 (1)
- ❌ Kyle Out (probably) overlaps
- **4 negatives + tentative overlap = HIGHEST PRIORITY.** No sent mail trail to resolve.

**Tony's Pizza (Wed Jun 3)**
- ❌ Site stale (1)
- ❌ No calendar event (1)
- ⚠️ Wednesday = weekday gig (advisory only, not a compounding signal)
- **2 negatives = elevated uncertainty.** Lower priority than May 30 because no member-out overlap.

**Harry's Night Club (Fri Jun 5) — formerly Leashless**
- ❌ Site stale (1)
- ✅ Calendar (Mike-created, 9pm-midnight)
- ✅ Venue folders exist for BOTH Harry's AND Leashless (confirms venue change)
- ✅ Sent mail confirms change
- ✅ No member conflicts
- **1 negative — solid.** Change is confirmed.

**Tony's Pizza (Sat Jun 6)**
- ❌ Site stale (1)
- ✅ Calendar (Mike-created, 7pm-midnight)
- ✅ Venue folder exists
- ✅ No member conflicts
- **1 negative — solid.** Calendar-confirmed date.

**Cruisery (Fri Jun 12)**
- ❌ Site stale (1)
- ✅ Calendar (Alfred-created — trusted per band member rule)
- ✅ No member conflicts
- **1 negative — solid.**

**Fess Parker Winery (Sat Jun 13)**
- ❌ Site stale (1)
- ✅ Calendar (Mike-created, 3-4pm)
- ✅ No member conflicts
- **1 negative — solid.**

### New Patterns from This Session

1. **Multiple-date venue gaps**: The Tony's Pizza case showed 2/3 Band Sheet dates missing from the calendar simultaneously. This is a stronger staleness signal than single-date gaps — it suggests bulk-entered dates that never materialized. Previously the skill only covered individual missing dates (Pitfall #11). Patched SKILL.md with a new subsection under Pitfall #11.

2. **No sent mail trail for venue booking**: Sent mail searches for "Tony" and "Figueroa" returned nothing, meaning those bookings were confirmed outside email. This is a useful negative signal — when sent mail is silent AND the calendar is silent for specific dates, those dates stay uncertain regardless of what the Band Sheet says.

3. **Weekday gig on Band Sheet with no calendar support**: Jun 3 (Wednesday) Tony's is unusual timing + no calendar event. The weekday flag is advisory, not compounding, but combined with the missing event it reaches 2 negatives = elevated uncertainty.

4. **Pattern consistency**: Every sesion in this worked-example document (May 21, 22, 23) has shown the Band Sheet at 9-11 days stale. The "1 negative" from staleness now applies to every listing by default. This should be the baseline assumption: **the Band Sheet is always stale until proven otherwise.** Future sessions should treat the initial 1-negative flag as a permanent fixture rather than a notable finding.

### Summary of skills-and-patterns changes after this session

- Added **resolution path** for email date mismatches (calendar check → sent mail check → uncertain)
- Added **resolution path** for email time mismatches (creator-based authority hierarchy)
- These patches mean future sessions won't have to invent resolution logic — they follow the ordered decision tree.
- Added **multiple-date venue gap pitfall** to SKILL.md (Pitfall #11 subsection) — systematic staleness pattern when the same venue has 2+ Band Sheet dates missing from calendar. Compounding assessment gives per-venue patterns extra weight.
- Confirmed that **no sent mail trail** is itself a meaningful signal (negative finding), elevated uncertainty when combined with calendar silence.

---

## Session 5: May 23, 2026 (evening) — Same-Day Repeat Pulse Check

This session ran at 21:47 PT, roughly 7 hours after Session 4. It is the first documented **same-day repeat briefing** — a scenario not explicitly covered in earlier skill iterations.

### Key Observation

Nothing had changed. The same calendar, same emails, same stale Band Sheet. The pulse check confirmed every finding from earlier in the day.

### What This Means for Future Sessions

1. **Multiple briefings in one day are normal** when the schedule demands it. Mike may trigger the monitor at any time via cron or manually.
2. **When nothing changed between sessions**, the correct response is brief confirmation of status quo, not a full re-report. The Quick Pulse Check variant handles this well — ~4-8 conversational lines covering unchanged but noteworthy items.
3. **The full fetch cycle still runs** on every session (calendar, Band Sheet, email sweep, pending approvals, sent mail checks). Never skip the data collection even when the output is brief, because a change might have just landed.
4. **The pending approvals file should be re-checked each session** even within the same day. In this session it still contained only the empty session log — clean. But if a garbled auto-reply draft had been added by an intervening monitor run, it would need cleanup.
5. **The Freshground iCal feed metrics had ticked up slightly** (2,909 → 2,910 VEVENTs) confirming the feed is actively maintained and growing ~1 event/day. This micro-change is worth noting in the feed health reference but not in the briefing to Mike.

### Practical Takeaway

When a same-day repeat session finds nothing changed:
- Report the status quo concisely in Neon's voice
- Do NOT re-analyze every compounding signal unless a specific date is now within the 2-week window that wasn't before
- Do NOT timestamp-hunt — saying "still the same, no new emails" is sufficient
- The compounding assessment from the morning session is still valid for the entire day unless a new event lands on the calendar

This pattern will recur. The skill should expect same-day repeats and handle them gracefully (brief, low-effort, confirmation-focused) rather than full deep-dive each time.

### Important status signal: email silence

When the booking email pipeline is quiet for a sustained period (10+ days with no new messages from any booking contact), the correct behavior is to report it concisely in the pulse check — not to search harder. "No new booking emails since [date]" is useful context for Mike. It means no news is good news, and no action is needed. See Session 8 where the pipeline had been quiet since May 15 (11 days).

---

## Session 6: May 24, 2026 — Quick Pulse Check (Cron-Fired)

### Setup
- **Date**: Sunday, May 24, 2026
- **Type**: Quick pulse check (cron-fired, no user present)
- **Band Sheet**: May 12 (12 days stale)
- **Pending approvals**: Empty session log only (clean)
- **Monitor script**: Returned 0 events (standard cron OAuth hang — expected, proceeded with inline OAuth)

### Quick Pulse Check — What Was Done vs Full Briefing

Per the skill's Quick Pulse Check Variant (SKILL.md):

| Step | Done? | Notes |
|---|---|---|
| Calendar fetch (inline OAuth) | ✅ Yes | 18 events found, 60-day window |
| Band Sheet fetch | ✅ Yes | Assessed staleness immediately (12 days) |
| Email sweep (per-contact) | ✅ Yes | 8 messages across 4 contacts |
| Pending approvals check | ✅ Yes | Clean, empty log |
| Sent mail for venue name mismatch | ✅ Yes | Found Harry's confirmation |
| Freshground calendar fetch | ✅ Yes | Found May 26 rehearsal |
| Deep compounding for >2 weeks out | ❌ Skipped | Pulse check rule: only next 14 days get full treatment |
| Freshground sent mail cross-ref | ✅ Done | Found 5 sent mails, only 1 rehearsal request (May 21). May 26 rehearsal has no sent mail trail. |
| Venue folder checks for >2 weeks | ❌ Skipped | Pulse check rule |
| Description field inspection on far-future events | ❌ Skipped | Pulse check rule |

### Calendar Findings (inline OAuth, 60-day window, 18 events)

| Date | Event | Creator | Notes |
|---|---|---|---|
| May 23-24 | Alfred Out | neonblondevc@gmail.com | Ends today |
| May 23-26 | Curtis Out | neonblondevc@gmail.com | Ends Tuesday |
| Wed May 27, 6-8:30pm | Santa Barbara Yacht Club | neonblondevc@gmail.com | NOT on Band Sheet |
| Fri May 29, 6-9pm | Figueroa Mountain (SB) | neonblondevc@gmail.com | Location: Santa Barbara |
| May 30-31 | Kyle Out (probably) | kyle.fegley@gmail.com | Tentative, overlaps with Tony's listing |
| Fri Jun 5, 9pm-midnight | Harry's Night Club (Pismo) | neonblondevc@gmail.com | Band Sheet says Leashless |
| Sat Jun 6, 7pm-midnight | Tony's Pizza (Ventura) | neonblondevc@gmail.com | ✅ Matches Band Sheet |
| Fri Jun 12, 9-11pm | Cruisery (SB) | 4lfred20@gmail.com | Alfred-created |
| Sat Jun 13, 3-4pm | Fess Parker Winery | neonblondevc@gmail.com | Short slot |
| Jun 18-19 | DAVE OUT | neonblondevc@gmail.com | Future |
| Jun 20-28 | Dave Out | neonblondevc@gmail.com | Multi-day |
| Jun 27-Jul 3 | Alfred Out | 4lfred20@gmail.com | Self-marked |
| Jul 3-4 | Dave Out | neonblondevc@gmail.com | |
| Jul 3-6 | Kyle Out | kyle.fegley@gmail.com | |
| Jul 8-16 | Mike Out | neonblondevc@gmail.com | Vacation |
| Jul 9-13 | Kyle OUT | neonblondevc@gmail.com | |
| Jul 11-12 | Dave Out | neonblondevc@gmail.com | |
| Jul 18, 6-9pm | Leashless | neonblondevc@gmail.com | One confirmed future Leashless |

### Email Sweep

| Contact | Messages | Key Content |
|---|---|---|
| rockstarentertainment805 | 2 (May 11) | Festival inquiry. Mike gave thumbs up. Phillip replied 👍. Resolved, contact is working on it. |
| jefftl123 | 4 (May 12-15) | Wedding contract (Sep 6). Jeff signed May 15, Mike asked for re-send May 19. **Stalled** — no reply since. |
| thebikeguyiv | 1 (May 11) | Date list: Fig Mtn 7-10pm, Tony's 5/31 tentative, Tony's 6/6 7-10, Fox Wine 4-7. **Date mismatch**: Bike Guy says 5/31 tentative VS Band Sheet says 5/30 confirmed. |
| Alfred | 1 (May 8) | Sin Chonies daily check — non-booking false positive |

**UNSEEN safety net**: 0 unseen messages outside known contacts.

### Sent Mail Resolution

| Search | Result |
|---|---|
| `SUBJECT "Harry"` | ✅ Found: "Updated Bandsheet Graphics — Harry's Nightclub" (May 19, to Alfred). Confirms Leashless → Harry's change. |
| `SUBJECT "Yacht"` | ❌ No results. Yacht Club booked outside email. |
| `SUBJECT "Bandsheet"` | ✅ Found: Same Harry's email (most recent bandsheet discussion). |
| `TO freshgroundrecords` | 5 sent mails found. Only 1 rehearsal request (May 21). The May 26 rehearsal on Mark's calendar has no email trail. |
| Rehearsal filtered by subject "rehearsal" / "Rehearsal" | 1 message found: the May 21 request (May 18). Confirms pattern: most Freshground sent mail is admin. |

### Compounding Assessment (Next 14 Days: May 24 — June 7)

| Gig | Negatives | Tentative Overlap? | Verdict |
|---|---|---|---|
| Santa Barbara Yacht Club (Wed 5/27) | 2 (stale site + not on Band Sheet) | No | Elevated uncertainty — flag as advisory |
| Figueroa Mountain (Fri 5/29) | 1 (stale site) | No | Solid — sent mail time mismatch resolved via creator authority |
| Tony's Pizza (Sat 5/30) | 4 (stale + no calendar event + no venue folder + email date mismatch) | Yes (Kyle Out probably) | **HIGHEST PRIORITY** — needs Mike's attention |
| Harry's Night Club (Fri 6/5) | 1 (stale site) | No | Solid — sent mail confirmed change from Leashless |
| Tony's Pizza (Sat 6/6) | 1 (stale site) | No | Solid — calendar-confirmed |

### Key Patterns from This Session

1. **Band Sheet at 12 days stale** — The compounding signal assessment is now best thought of as "every listing starts with 1 negative just from being on a stale page." Only dates that also have strong calendar + folder + sent mail support can be called solid.

2. **Bike Guy emails need cross-referencing every time**: His date lists consistently differ from the Band Sheet in at least one dimension (time or date). The Fig Mtn time mismatch was harmless (calendar overrides). The Tony's 5/30 vs 5/31 mismatch is critical — the absence of any calendar event or venue folder means the Band Sheet's May 30 date has zero corroborating evidence.

3. **Negative sent mail results are as valuable as positive ones**: Searching for "Tony" in sent mail and finding nothing means there's no paper trail for the May 30 date. Combined with no calendar event, the date stays fully UNCERTAIN. The skill's resolution path now covers this explicitly, but this session confirmed the real-world application.

4. **Rogue venue folder detected**: `Kyle Out - 7 3 2026` in `/Venues/`. The skill's pitfall (Step 9) warns about this pattern. It exists on disk and should be flagged for cleanup.

5. **Freshground sent mail mostly admin**: 5 sent mails to freshgroundrecords, only 1 rehearsal request. The rest were GoDaddy DNS, website calendar fix, Google Workspace config. This confirms the skill's note that filtering by rehearsal subject keywords is essential.

6. **Venue folder naming confirmed**: ALL 23 folders use `Venue Name - M D YYYY` (space-separated, no leading zeros). Examples: `Tony's Pizza - 5 30 2026`, `Santa Barbara Yacht Club - 5 27 2026`. No `YYYY-MM-DD` folders exist on disk (the create_venue_package.sh script produces that format but hasn't been run yet).

7. **Scan for ALL Neon Blond rehearsals on Freshground, not just the requested one**: After finding the first rehearsal matching a sent mail request, do a broader scan of all upcoming Neon Blond events on Mark's calendar. In Session 8, the May 26 rehearsal (confirmed via sent mail search) led to ALSO finding Jun 2 — a standing arrangement with no email trail. Both should be reported together.

7. **Cron-delivered pulse check format**: The output should be the same quality as interactive. The system auto-delivers the agent's final response — no send_message needed. Include MEDIA: if relevant but text-only is fine for pulsed briefings.

---

## Session 7: May 25, 2026 — Quick Pulse Check (Cron-Fired)

### Setup
- **Date**: Monday, May 25, 2026
- **Type**: Quick pulse check (cron-fired, no user present)
- **Band Sheet**: May 12 (13 days stale — longest in any session so far)
- **Pending approvals**: **Hybrid state** — not purely an empty session log and not purely a draft queue. The monitor script produced `{"calendar_events": [], "new_messages": [calendar notification], "replies": [garbled auto-reply]}` — the `calendar_events` array was empty (session-log pattern) but the `replies` array had content (garbled-auto-reply pattern). This is a novel edge case: the monitor script added a false-positive auto-reply on the same run that also produced a session-log skeleton.
- **Monitor script**: Returned 0 events (standard cron OAuth hang — expected, proceeded with inline OAuth)

### Phase 3 Edge Case: Hybrid pending_approvals.json

The file looked like a session log at first glance (`calendar_events: []`) but actually contained actionable garbled content in `replies`. The `calendar-notification@google.com` sender was auto-classified as a booking inquiry, generating this garbled auto-reply draft:

```json
{
  "replies": [{
    "to": ["calendar-notification@google.com"],
    "subject": "Re: Daily Agenda for Neon Blonde as of 5am",
    "body": "Hey Google Calendar,\n\nHere's the status on those dates you mentioned:\n  - May 25 — ✅ Looks open! Let's lock it in.\n\nI'll follow up with Mike and get back to you soon.\n\n- Neon"
  }]
}
```

**Resolution**: Per the established Phase 3 rule for `calendar-notification@google.com`, the draft was auto-discarded immediately and the file cleared down to an empty session log. Mentioned briefly in the briefing ("Cleared a stale false-positive draft").

**What makes this novel**: Previous sessions had the file as either:
- Purely an empty session log (no action needed)
- Purely a draft queue with garbled entries (needs review)

Session 7 had **both patterns combined** — a session-log skeleton with garbled content inside it. The rule "only entries with non-empty `replies` arrays or explicit draft objects need review" correctly triggered review. The per-sender auto-discard rule for `calendar-notification@google.com` correctly identified it as noise. The combination of rules handled it without needing a new rule, but future sessions should recognize this hybrid structure as normal monitor-script behavior rather than treating it as anomalous.

**Detection heuristic**: If any `replies` entry exists AND the `to` field contains an auto-discard domain (`calendar-notification@google.com`, `no-reply@accounts.google.com`, etc.), it is safe to auto-clear without reviewing individual reply content. The `to` field is the fastest signal — checking it avoids having to parse garbled auto-reply body text.

### Calendar Findings (inline OAuth, 60-day window)

| Date | Event | Creator | Notes |
|---|---|---|---|
| May 23-26 (Sat-Tue) | Curtis Out | neonblondevc@gmail.com | All-day, end date exclusive → covers May 23-26 |
| Wed May 27, 6-8:30pm | Santa Barbara Yacht Club | neonblondevc@gmail.com | NOT on Band Sheet. Location: "Santa Barbara" |
| Fri May 29, 6-9pm | Figueroa Mountain | neonblondevc@gmail.com | Location: "Santa Barbara " (trailing space in field) |
| May 30-31 (Sat-Sun) | Kyle Out (probably) | kyle.fegley@gmail.com | Tentative, overlaps no confirmed gig |
| Fri Jun 5, 9pm-midnight | Harry's Night Club & Beach Bar (Pismo) | neonblondevc@gmail.com | Band Sheet still says Leashless (Ventura) @6pm |
| Sat Jun 6, 7pm-midnight | Tony's Pizza (Ventura) | neonblondevc@gmail.com | ✅ Matches Band Sheet |
| Fri Jun 12, 9-11pm | Cruisery (SB) | 4lfred20@gmail.com | Alfred-created, ✅ matches Band Sheet |
| Sat Jun 13, 3-4pm | Fess Parker Winery | neonblondevc@gmail.com | ✅ Matches Band Sheet |
| Jun 18-28 | Dave Out (multiple events) | neonblondevc@gmail.com | Future |
| Jun 27-Jul 3 | Alfred Out | 4lfred20@gmail.com | Self-marked |
| Jul 8-16 | Mike Out | neonblondevc@gmail.com | Vacation |
| Jul 18, 6-9pm | Leashless | neonblondevc@gmail.com | One confirmed future Leashless date |

### Freshground Calendar

- **Tue May 26**: `- 10 Neon Blond` (7-10pm Pacific) — rehearsal night before SB Yacht Club gig
  - No sent mail trail for this date (consistent with Session 2-6 findings)
  - **Rehearsal availability check**: Curtis is still out (May 23-26), so he won't be at this rehearsal. Flagged in briefing.
  - **Rehearsal-gig conflict check**: No conflict — rehearsal is Tue May 26, next gig is Wed May 27 (different days)
- 102 events in 2026, 2910 VEVENTs total — consistent with Session 6's feed measurements

### Email Sweep

| Contact | Latest | Status |
|---|---|---|
| Phillip Thomas (rockstar) | May 11 "Festivals" | Resolved — no new messages |
| Jeff (jefftl123) | May 15 "Wedding Contract" | Still stalled — no reply since May 15 despite Mike's May 19 request |
| thebikeguyiv (Phillip) | May 11 "Dates from..." | No new messages. Date list unchanged |
| Alfred (sin.chonies) | May 8 daily check | False positive (archived) |

**UNSEEN safety net**: 1 unseen message — the calendar notification (already caught and discarded in Phase 3). No other noise.

### Sent Mail Resolution

| Search | Result | Notes |
|---|---|---|
| `SUBJECT "Harry"` | ✅ Found: "Updated Bandsheet Graphics — Harry's Nightclub" (May 19, to Alfred) | Confirms Leashless→Harry's change, same as Sessions 2-6 |
| `TO "freshgroundrecords" SUBJECT "rehearsal"` | 1 message: May 21 rehearsal request (May 18) | May 26 rehearsal has no sent mail trail — consistent pattern |
| `TO "freshgroundrecords" SINCE 20-May` | 0 results | No new sent mail to Mark since the May 21 request |

### Venue Folder Check (Next 14 Days)

| Venue | Folder Exists? | Notes |
|---|---|---|
| Santa Barbara Yacht Club - 5 27 2026 | ✅ Yes | ✅ |
| Figueroa Mountain - 5 29 2026 | ✅ Yes | ✅ |
| Harry's Night Club & Beach Bar - 6 5 2026 | ✅ Yes | Created May 19 |
| Leashless - 6 5 2026 | ✅ Yes | Old name still on disk |
| Tony's Pizza - 6 6 2026 | ✅ Yes | ✅ |

**Rogue folder detected**: `Kyle Out - 7 3 2026` in Venues directory — consistent with Step 9 pitfall. Flagged in briefing.

### Compounding Assessment (Next 14 Days: May 25 — June 8)

| Gig | Negatives | Tentative Overlap? | Verdict |
|---|---|---|---|
| Santa Barbara Yacht Club (Wed 5/27) | 2 (stale site + not on Band Sheet) | No | Elevated uncertainty — flag as advisory (consistent with prior sessions) |
| Figueroa Mountain (Fri 5/29) | 1 (stale site) | No | Solid — calendar + folder + no member conflicts |
| Tony's Pizza (Sat 5/30) | 4 (stale + no calendar event + no venue folder + email date mismatch) | Yes (Kyle Out probably) | **HIGHEST PRIORITY** — unchanged from Sessions 1-6 |
| Harry's Night Club (Fri 6/5) | 1 (stale site) | No | Solid — sent mail + both folders + calendar confirm |
| Tony's Pizza (Sat 6/6) | 1 (stale site) | No | Solid — calendar + folder + no member conflicts |

### Key Patterns from This Session

1. **Band Sheet now 13 days stale** — longest observed lag, but every gig listing that had calendar + folder backing remained solid. The staleness penalty is predictable and consistent; it doesn't degrade confidence further after ~10 days.

2. **Hybrid pending_approvals.json structure** — a session log skeleton (`calendar_events: []`) combined with garbled auto-reply content (`replies: [calendar notification draft]`). This is a monitor script behavior where it returns 0 events (cron OAuth hang) but still processes UNSEEN emails and generates garbled auto-replies. The existing rules (non-empty replies = review, calendar-notification sender = auto-discard) handle it correctly together. Added a detection heuristic: check the `to` field of any reply entry for auto-discard domains before reviewing the garbled body text.

3. **Figueroa Mountain location field** had trailing whitespace (`"Santa Barbara "`). This is a Google Calendar data entry artifact. Not a briefing blocker but worth stripping when cross-referencing city names internally.

4. **Rehearsal-vs-member-out cross-reference** worked correctly: Curtis is out through May 26 (all-day event, end date exclusive), so he can't attend the May 26 rehearsal. This is the first explicit documentation of member-out affecting rehearsal attendance (previous sessions only checked rehearsal vs gig conflicts, not rehearsal vs member-out). The skill's Quick Pulse Check section mentions this check; this session confirmed it works as designed.

5. **No email traffic from any booking contact** since May 15. The booking pipeline has been quiet for 10 days. This is useful context for Mike — no news on the Jeff contract, no word from Phillip on festivals, no new Bike Guy dates since May 11.

6. **All prior patterns confirmed stable**: stale Band Sheet, Harry's/Leashless venue change, Jeff stuck on contract, no sent mail trail for May 26 rehearsal. The compounding assessment for every gig is unchanged since Session 6.

### Summary of Changes After Session 7

- **Added detection heuristic** for hybrid pending_approvals.json structure: check the `to` field of any reply entry for auto-discard domains before reviewing garbled body text. This saves parsing effort on clearly-false-positive entries.
- **Documented rehearsal-vs-member-out cross-reference** as a live check that fired correctly in this session (Curtis out overlaps with May 26 rehearsal).
- **Confirmed** that the Figueroa Mountain location may have trailing whitespace — added a note to strip whitespace when cross-referencing city names internally.

---

## Session 8: May 26, 2026 — First Fresh Band Sheet Case

See `references/session-8-may-26.md` for the full session write-up.

**Key novelties**:
- **Band Sheet was fresh** (May 25, 1 day old) — first time in documented history. Flipped the baseline for compounding assessment.
- **OAuth token fully dead** (`invalid_grant`) — distinct from `invalid_client` (secret rotated). First session where inline OAuth failed entirely.
- **Two Neon Blond rehearsals found** (May 26 AND Jun 2) — confirmed the "scan for all upcoming" pattern.
- **Email pipeline quiet since May 15** — no new booking emails for 11 days.

### What This Means for Future Sessions

1. **Don't assume persistent staleness**: The Band Sheet can go from 13 days stale to 1 day fresh between sessions. Always check the `updated` field fresh each time.

2. **Prepare for OAuth to die between sessions**: The token worked for 7 consecutive sessions, then died on the 8th. Always have the Band Sheet fallback ready.

3. **Expect a quiet period**: After a flurry of booking activity (May 11-15), the pipeline went silent. Report this as useful context, not a problem to solve.
