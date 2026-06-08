# Band Sheet JSON Data Endpoint

The Band Sheet website at `mlmil.github.io` is a React app that fetches data from a static JSON file.
You can bypass browser rendering entirely by fetching the JSON directly.

## Endpoint

```
https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json
```

Append a cache-busting query parameter: `?v=${Date.now()}` or `?v=<unix_timestamp>`.

## What You Get

The JSON response contains these fields:

```json
{
  "updated": "May 25, 2026 @ 9:23 AM PT",
  "this_week": [
    "WEDNESDAY @6PM Santa Barbara Yacht Club, Santa Barbara",
    "FRIDAY @6PM Figueroa Mountain, Santa Barbara",
    "KYLE OUT SATURDAY"
  ],
  "booked_gigs": [
    "WED 5-27-2026 @6PM — Santa Barbara Yacht Club, Santa Barbara",
    "FRI 5-29-2026 @6PM — Figueroa Mountain, Santa Barbara",
    ...
  ],
  "members_out": [
    "- Alfred: SAT 6-27-2026 to THU 7-2-2026",
    ...
  ],
  "free_weekends": [
    "- SUN May 31",
    "- SUN June 7",
    ...
  ]
}
```

## Fastest Access (curl)

```bash
curl -s "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json?v=$(date +%s)"
```

## From Python

```python
import urllib.request, json
resp = urllib.request.urlopen(
    "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json",
    timeout=15
)
data = json.loads(resp.read().decode('utf-8'))
print("Updated:", data['updated'])
print("Next 2 weeks:", data['this_week'])
```

## Using web_extract

```python
from hermes_tools import web_extract
result = web_extract(urls=['https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json'])
# result['results'][0]['content'] has the JSON text
```

## Why Use This Instead of Browser

| Method | Time | Reliability |
|--------|------|-------------|
| Browser navigate + render | 5-15s | Depends on CDP/browser availability |
| curl JSON endpoint | 0.5-2s | Always works, no rendering needed |
| web_extract | 1-3s | Reliable |

**Two caveats:**
1. **Always check the `updated` field first.** If the JSON hasn't been updated recently (>4 days), treat the data as possibly stale and cross-reference aggressively — same as checking the page footer.
2. **The `free_weekends` list only checks gig conflicts, NOT member availability.** Cross-reference member-out events from the calendar before calling any day open. This is equivalent to the website's "Weekend Days Open" list — same limitation.

## The `this_week` Field

The JSON includes a `this_week` array with quick near-term context that's not in the structured fields:

```json
"this_week": [
    "WEDNESDAY @6PM Santa Barbara Yacht Club, Santa Barbara",
    "KYLE OUT SATURDAY"
]
```

This is useful for a quick pulse check — it's a curated shortlist of what's immediately relevant. Use it as a fast entry point, but still verify against the calendar and structured `booked_gigs`/`members_out` for completeness.

## ⚠️ Pitfall — Entries Are Strings, Not Dicts

All entries in `booked_gigs`, `members_out`, and `free_weekends` are **plain strings**, not structured objects. Do NOT try `.get('date')` or `.get('venue')` on them — you'll get `AttributeError: 'str' object has no attribute 'get'`.

### Parsing dates from `booked_gigs` entries

Format: `"FRI 6-5-2026 @9PM — Venue Name, City"`

```python
import re
from datetime import date

for g in data['booked_gigs']:
    m = re.search(r'(\d+)-(\d+)-(\d{4})', g)
    if m:
        gig_date = date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        # gig_date is a proper date object for comparison
```

### Parsing dates from `members_out` entries

Format: `"- Alfred: SAT 6-27-2026 to THU 7-2-2026"` or `"- Kyle: TUE 6-2-2026"`

```python
dates = re.findall(r'(\d+)-(\d+)-(\d{4})', entry)
# Returns list of (month, day, year) tuples — use first and last for ranges
```

## Browser Fallback

If the JSON endpoint ever returns a 404 (site structure changed), fall back to browser navigation:
- `https://mlmil.github.io/NeonBlonde-Bandsheet/docs/`
- The React site fetches the same JSON internally and renders it
