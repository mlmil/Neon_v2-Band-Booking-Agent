# Freshground Sound — Mark's Calendar

## Calendar Info
- **URL (embed view)**: `https://calendar.google.com/calendar/embed?src=freshgroundrecords@gmail.com`
- **Calendar ID**: `freshgroundrecords@gmail.com`
- **Timezone**: America/Los_Angeles (Pacific, UTC-7)
- **Public**: Yes — no auth needed. iCal feed and embed both work.

## How to Read It

### Option A: Public iCal Feed (fast, preferred)
```python
import urllib.request, re
from datetime import datetime, timedelta, timezone

pacific = timezone(timedelta(hours=-7))
resp = urllib.request.urlopen(
    "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics",
    timeout=10
)
data = resp.read().decode('utf-8')

events = re.split(r'BEGIN:VEVENT', data)
for ev in events[1:]:
    lines = ev.split('\n')
    dtstart_line = next((l for l in lines if l.startswith('DTSTART')), None)
    summary = next((l.replace('SUMMARY:', '').strip() for l in lines if l.startswith('SUMMARY:')), None)
    if not dtstart_line or not summary:
        continue

    m = re.match(r'DTSTART(?:;VALUE=DATE)?:(\d{4})(\d{2})(\d{2})T?(\d{2})?(\d{2})?(\d{2})?', dtstart_line)
    if not m:
        continue

    yr, mo, dy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh, mm = m.group(4) or '00', m.group(5) or '00'
    is_date_only = 'VALUE=DATE' in dtstart_line
    is_utc = 'Z' in dtstart_line if not is_date_only else False

    if is_date_only:
        dt_pac = datetime(yr, mo, dy, tzinfo=pacific)
    elif is_utc:
        dt_u = datetime(yr, mo, dy, int(hh), int(mm), tzinfo=timezone.utc)
        dt_pac = dt_u.astimezone(pacific)
    else:
        dt_pac = datetime(yr, mo, dy, int(hh), int(mm), tzinfo=pacific)

    # Now dt_pac is the correct Pacific time
    # Check if it falls in your date range
```

### Option B: CamoFox Browser Snapshot (fallback)
```
mcp_camofox_browser_camofox_create_tab(url="https://calendar.google.com/calendar/embed?src=freshgroundrecords@gmail.com&ctz=America/Los_Angeles&pli=1")
mcp_camofox_browser_camofox_snapshot(tabId="<tabId>")
```

## Quick Scan with grep

The iCal feed contains ~2900 events dating back to 2013. For most briefing tasks (checking if a specific date is booked, finding "Neon Blond" events), full Python parsing is overkill. Use `grep` to quickly filter:

```bash
# Find all events in May/June 2026
curl -s "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics" \
  | grep -E "^(DTSTART|SUMMARY|DTEND)" \
  | grep -A1 -B1 "20260[56]" \
  | head -60
```

The `20260[56]` pattern matches May (05) or June (06) of 2026. Adjust the year/month pattern as needed.

### Finding Neon Blond entries specifically
```bash
curl -s "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics" \
  | grep -B2 -A2 -i "Neon Blond"
```

This outputs VEVENT blocks for all Neon Blond rehearsals. Use `-i` for case-insensitive matching because Mark's calendar spells it both "Neon Blond" (no 'e') and "Neon Blonde" (with 'e') across different events. Both spellings exist in the data — always use case-insensitive search or just filter by `'Neon' in ev` to catch both.

**Pitfall — grep for exact "Neon Blond" misses "Neon Blonde" events**: Some older/recurring events use the full name "Neon Blonde". Always use `-i` flag or broader `Neon` substring match to avoid missing half the rehearsals.

### Checking if a specific requested date was added
After Mike sends a rehearsal request, check Mark's calendar for confirmation:

```bash
curl -s "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics" \
  | grep -B2 -A2 "Neon Blond" \
  | grep -A2 "20260521"  # replace with the date you're checking
```

If the event was created on the same day Mike sent the request (check the `CREATED` or `LAST-MODIFIED` field), Mark confirmed it by adding it to his calendar — no reply needed.

**Pitfall — stale feed cache**: The public iCal feed may cache for a few minutes. If you just saw Mark create the event but it doesn't appear in the feed yet, wait 30-60 seconds and retry before falling back to browser embed.

## Year Filtering
The feed serves events from 2014 onward — 10+ years of history. Always filter by current year when parsing:

```python
if yr == CURRENT_YEAR and mo == CURRENT_MONTH and day_in_range:
    process_event()
```

## Real-Data Examples (verified May 21, 2026)

As of May 2026, the feed contains ~2900 VEVENTs total. Current 2026 data is present alongside historical events from 2013-2017. Here are concrete examples of what you'll see:

### Event: `- 10 Neon Blond` on Thursday, May 21 (rehearsal tonight)
```
BEGIN:VEVENT
DTSTART:20260522T020000Z
DTEND:20260522T050000Z
SUMMARY:- 10 Neon Blond
```
- `DTSTART:20260522T020000Z` = **May 21, 7:00pm Pacific** (UTC midnight minus 7 = previous evening)
- `DTEND:20260522T050000Z` = **May 21, 10:00pm Pacific**
- Number prefix `10` in the summary = event ends at 10pm Pacific ✓
- Duration: 3 hours (7-10pm)

### Event: `- 10 Neon Blond` on Tuesday, May 26 (another rehearsal)
```
BEGIN:VEVENT
DTSTART:20260527T020000Z
DTEND:20260527T050000Z
SUMMARY:- 10 Neon Blond
```
- Same pattern: 7-10pm Pacific, 3-hour block, end-time 10 matches the `- 10` prefix.

### Historical event (for comparison, still in feed)
```
BEGIN:VEVENT
DTSTART:20260211T030000Z
DTEND:20260211T060000Z
SUMMARY:- 10 Neon Blonde
```
- February 10, 2026, 7-10pm Pacific (UTC→Pacific rollback confirmed)
- Note: uses "Neon Blonde" (with 'e') — the `-i` grep flag catches both spellings.

### Confirmed feed health indicators (current as of May 24, 2026)
| Metric | Value |
|---|---|
| Total VEVENTs | 2,911 |
| Oldest events | 2013 (10+ years retained) |
| Newest events | May 2026 (current) |
| "Neon" events in 2026 | ~5 confirmed |
| Year filter needed? | Yes, always filter by `DTSTART:2026` |
| Pacific rollback (UTC→PDT) | -7 hours, events land on previous day evening |
| Growth rate | +1 event/day (~2909→2911 in ~72h) — feed is actively maintained |

**Key takeaway**: The feed is alive and current as of May 2026. If you see only 2013-2016 events when you fetch it, you're not filtering by year correctly — the current data is there, just buried. If you've filtered by year and still see nothing, then try the browser embed fallback.

## Event Name Convention

Events follow the pattern `- <number> <name>` — e.g. `- 10 David Arel`.

**The number prefix is the END TIME** (hour or hour:minute in 12-hour format, Pacific):
- `- 4 David A.` → ends at 4:00pm Pacific
- `- 10 Neon Blond` → ends at 10:00pm Pacific
- `- 7 Sean` → ends at 7:00pm Pacific

**⚠️ Common start-time rule**: For regular rehearsals (especially Neon Blond), the typical duration is 3 hours. So `- 10 Neon Blond` = 7:00-10:00pm. The number is the END, subtract ~3 hours for a reasonable start estimate. For `- 9 Neon Blond` = 6:00-9:00pm.

**⚠️ Decimal-minute edge case**: Some events use hours + minutes, e.g. `- 12:30 Kevin M.` — this means ends at 12:30pm Pacific. The regex for extracting the end time should handle both `- H` and `- H:MM` patterns. Use `r'- (\d{1,2}(?::\d{2})?) '` (captures optional `:MM` suffix) instead of `r'- (\d+) '` (whole-number only) to avoid truncating `12:30` to just `12`.

```python
# Correct: captures hours with optional minutes
m = re.search(r'- (\d{1,2}(?::\d{2})?) ', summary)
if m:
    end_time = m.group(1)  # "10" or "12:30"
    print(f"Ends at {end_time}pm Pacific")
```

Not all events follow this pattern (e.g. `Cash Cats @ TONYS` is a show with no number prefix).

## CLOSED / All-Day Events (Studio Closed Days)

Mark's calendar uses all-day events (no time component) for bookkeeping entries — notably **CLOSED** days when the studio is unavailable. These use `VALUE=DATE` format (no time):

```
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260525
DTEND;VALUE=DATE:20260526
SUMMARY:CLOSED
```

**When checking rehearsal availability**, always filter out CLOSED days. An otherwise-open date on Mark's schedule is not truly available if the studio is closed.

### Quick grep for CLOSED days
```bash
curl -s "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics" \
  | grep -B2 -A1 "SUMMARY:CLOSED" \
  | grep -B2 -A1 "2026052[4-9]\|2026053\|202606"
```

Adjust the date range pattern to your month/week. The `B2` (2 lines before) captures `DTSTART` so you can see which day is closed.

### CLOSED event characteristics
- `VALUE=DATE` — no time component, occupies full day
- `SUMMARY:CLOSED` — exact title (sometimes `CLOSED` with Memorial Day or holiday note)
- End date is **exclusive** — `DTEND:20260526` means CLOSED through end of day 2026-05-25
- Observed instances: May 25, 2026 (Memorial Day) confirmed CLOSED

### Python check pattern
```python
# When scanning events for rehearsal availability:
if 'VALUE=DATE' in dtstart_line and 'CLOSED' in (summary or ''):
    # Mark's studio is closed this day — skip in availability
    continue
```

## Timezone Pitfalls

### ⚠️ CRITICAL: Don't group events by UTC date — convert to Pacific FIRST, then filter
This was the mistake made on May 25, 2026 when checking the calendar: grouping DTSTART by raw UTC date (`20260527` → May 27) BEFORE converting to Pacific mis-assigned the `- 10 Neon Blond` event (actually **Tuesday** May 26 at 7pm Pacific) to **Wednesday** May 27.

**Always follow this order:**
1. Parse the raw DTSTART string
2. Detect whether it's UTC (ends with `Z`) or date-only (`VALUE=DATE`)
3. Convert to Pacific datetime
4. **Then** filter/group by Pacific date

```python
# ❌ WRONG — groups by UTC date, mis-assigns evening events
event_date = datetime.strptime(dtstart_str[:8], '%Y%m%d').date()  # UTC!
if event_date == target_date:  # misses events that roll back to previous Pacific day

# ✅ CORRECT — convert to Pacific first, then filter
dt_u = datetime(yr, mo, dy, hh, mm, tzinfo=timezone.utc)
dt_pac = dt_u.astimezone(pacific)  # Pacific = UTC-7
if dt_pac.date() == target_date:  # correct Pacific day
```

### Same-evening, different-UTC-date trap
Two events on the same Pacific evening can have different UTC dates if one starts before and one after 07:00Z (midnight Pacific). On May 26, 2026:
- P&P: `DTSTART:20260526T230000Z` → May 26 **4pm Pacific**
- Neon Blond: `DTSTART:20260527T020000Z` → May 26 **7pm Pacific** (UTC says "27th" but Pacific is still "26th")

If you filter by UTC date `20260526`, you find P&P but miss Neon Blond. If you filter by UTC date `20260527`, you find Neon Blond but call it "Wednesday". **Both are Tuesday in Pacific time**.

The fix: convert BOTH timestamps to Pacific, then compare `.date()` to the target Pacific date.

### A reusable script exists
Instead of writing ad-hoc parsing each time, use the skill's built-in script. From anywhere:
```bash
python3 /Users/studio_hub/.hermes/skills/Neon_v1/scripts/check-freshground-calendar.py              # today
python3 /Users/studio_hub/.hermes/skills/Neon_v1/scripts/check-freshground-calendar.py 2026-05-26   # specific date
python3 /Users/studio_hub/.hermes/skills/Neon_v1/scripts/check-freshground-calendar.py --week        # next 7 days
```
This handles UTC→Pacific conversion, CLOSED day detection, and chronological sorting.

### UTC midnight events roll back one day in Pacific
An event with `DTSTART:20260525T000000Z` is **May 25 at midnight UTC**, which converts to **May 24 at 5:00pm Pacific** (the previous day). Always convert to Pacific before filtering by date.

Real example from the feed:
- `DTSTART:20260522T020000Z` → `2026-05-21 19:00:00-07:00` Pacific (previous day!)
- The day in the UTC timestamp (22nd) is NOT the same as the Pacific day (21st)

### Late-night shows
Shows at bars/venues often start late:
- `Cash Cats @ TONYS` at `DTSTART:20260530T053000Z` = **May 29 at 10:30pm Pacific** (UTC date is ahead)

### All-day events use VALUE=DATE
An event with `DTSTART;VALUE=DATE:20260525` has no time component — it's an all-day event. Treat these as occupying the full day in Pacific time.

## Booking Duration
Events typically run 2-3 hours, e.g.:
- `- 4 David A.` → 2:00pm to 4:00pm (2 hours)
- `- 10 Neon Blond` → 7:00pm to 10:00pm (3 hours)
- `- 7 Sean` → 5:00pm to 7:00pm (2 hours)
