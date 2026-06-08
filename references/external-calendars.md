# Reading External Public Calendars (No Auth Required)

When checking availability for venues, rehearsal spaces, or other contacts who
share a public Google Calendar, use the iCal feed — it requires zero auth.

## Pattern

1. Get the calendar's email address from the embed URL:
   `https://calendar.google.com/calendar/embed?src=FRESHGOUNDRECORDS@GMAIL.COM`
   → Calendar ID = `freshgroundrecords@gmail.com`

2. Convert to iCal URL:
   `https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics`
   (URL-encode the `@` as `%40`)

3. Fetch and parse with curl + Python inline:

```bash
curl -sL --max-time 10 \
  "https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics" \
  | python3 -c "
import sys
from datetime import date, datetime, timedelta

data = sys.stdin.read()
today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=7)

events = []
current = {}
in_event = False
for line in data.split('\r\n'):
    if line == 'BEGIN:VEVENT':
        in_event = True
        current = {}
    elif line == 'END:VEVENT':
        in_event = False
        events.append(current)
    elif in_event and ':' in line:
        key, _, val = line.partition(':')
        current[key] = val

found = False
for e in events:
    dtstart = e.get('DTSTART', '')
    if 'VALUE=DATE' in dtstart:
        dtstart = dtstart.split(':')[-1] if ':' in dtstart else dtstart
    else:
        dtstart = dtstart.split(':')[-1][:8] if ':' in dtstart else ''
    if not dtstart or len(dtstart) < 8:
        continue
    try:
        event_date = date(int(dtstart[:4]), int(dtstart[4:6]), int(dtstart[6:8]))
    except:
        continue
    if week_start <= event_date < week_end:
        found = True
        summary = e.get('SUMMARY', '(no title)')
        start_time = ''
        if 'T' in e.get('DTSTART', ''):
            raw = e['DTSTART'].split(':')[-1]
            if 'T' in raw and len(raw) >= 15:
                t = raw[9:15]
                h = int(t[:2])
                ampm = 'am' if h < 12 else 'pm'
                h12 = h % 12 or 12
                start_time = f' @ {h12}{ampm}'
        print(f'  {event_date.strftime(\"%a %b %-d\")}{start_time} — {summary}')

if not found:
    print('  No events this week.')
"
```

## Known External Calendars

| Who | Calendar ID | Purpose |
|-----|------------|---------|
| Mark Antaky / Freshground Sound | `freshgroundrecords@gmail.com` | Rehearsal space availability |

## Pitfalls

- The iCal feed returns ALL events (entire history). Always filter by date range.
- Google Calendar embed URLs use `src=EMAIL` — extract the email for the iCal URL.
- Don't try to use `web_extract` or browser navigate on the embed URL — Google blocks scraping. Use the iCal feed directly.
- The Google Calendar JSON API requires an API key, but the iCal feed does not.
