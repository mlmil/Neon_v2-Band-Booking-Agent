#!/usr/bin/env python3
"""
check-freshground-calendar.py — Check Mark's Freshground Sound calendar for a given date.

Usage:
    python3 check-freshground-calendar.py                     # shows events for today (Pacific)
    python3 check-freshground-calendar.py 2026-05-26          # specific date
    python3 check-freshground-calendar.py --week               # next 7 days
    python3 check-freshground-calendar.py 2026-05-26 --week    # 7 days starting from date

Output: events sorted by Pacific time, with CLOSED days flagged.
All DTSTART timestamps are converted from UTC to America/Los_Angeles before filtering.
"""

import urllib.request
import re
import sys
from datetime import datetime, timezone, timedelta, date

ICAL_URL = "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics"
PACIFIC = timezone(timedelta(hours=-7))  # PDT (March–November)


def parse_date(arg: str) -> date:
    """Parse YYYY-MM-DD or YYYYMMDD into a date object."""
    cleaned = arg.replace("-", "")
    return datetime.strptime(cleaned, "%Y%m%d").date()


def get_target_dates(args: list[str]) -> list[date]:
    """Return the list of dates to check based on CLI args."""
    today = datetime.now(PACIFIC).date()

    if not args or args[0] in ("--week",):
        # Default: today, or this week
        start = today
        if args and args[0] == "--week":
            pass  # start stays today
        # Check if there's a date before --week
        return [start + timedelta(days=i) for i in range(7)]

    # Parse leading date argument(s)
    dates = []
    i = 0
    while i < len(args) and args[i] != "--week":
        try:
            dates.append(parse_date(args[i]))
        except ValueError:
            print(f"⚠️  Can't parse '{args[i]}' as a date, skipping")
        i += 1

    if not dates:
        dates = [today]

    # Check if --week flag follows
    if "--week" in args:
        expanded = []
        for d in dates:
            expanded.extend(d + timedelta(days=i) for i in range(7))
        return expanded

    return dates


def fetch_ical() -> str:
    resp = urllib.request.urlopen(ICAL_URL, timeout=15)
    return resp.read().decode("utf-8")


def parse_events(ics: str) -> list[tuple[datetime, str, str, bool]]:
    """
    Parse VEVENTs from ICS data.
    Returns list of (dt_pacific, summary, raw_dtstart, is_closed_all_day)
    """
    blocks = re.split(r"BEGIN:VEVENT", ics)
    results = []

    for block in blocks[1:]:
        # Extract fields
        dtstart_m = re.search(r"DTSTART(?:;VALUE=DATE)?:([^\r\n]+)", block)
        dtend_m = re.search(r"DTEND(?:;VALUE=DATE)?:([^\r\n]+)", block)
        summary_m = re.search(r"SUMMARY:([^\r\n]+)", block)

        if not dtstart_m or not summary_m:
            continue

        raw = dtstart_m.group(1)
        summary = summary_m.group(1).strip()

        # Skip historical data (pre-2025)
        if raw[:4].isdigit() and int(raw[:4]) < 2025:
            continue

        is_date_only = "VALUE=DATE" in dtstart_m.group(0)
        is_utc = raw.endswith("Z") and not is_date_only

        m = re.match(r"(\d{4})(\d{2})(\d{2})T?(\d{2})?(\d{2})?", raw)
        if not m:
            continue

        yr, mo, dy = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hh = int(m.group(4) or 0)
        mm = int(m.group(5) or 0)

        if is_date_only:
            dt_pac = datetime(yr, mo, dy, tzinfo=PACIFIC)
        elif is_utc:
            dt_u = datetime(yr, mo, dy, hh, mm, tzinfo=timezone.utc)
            dt_pac = dt_u.astimezone(PACIFIC)
        else:
            # Already local (rare in this feed, but handle it)
            dt_pac = datetime(yr, mo, dy, hh, mm, tzinfo=PACIFIC)

        is_closed = is_date_only and summary.upper() == "CLOSED"
        results.append((dt_pac, summary, raw, is_closed))

    return results


def main():
    target_dates = get_target_dates(sys.argv[1:])
    ics = fetch_ical()
    events = parse_events(ics)

    for target_date in target_dates:
        day_events = []
        for dt_pac, summary, raw, is_closed in events:
            if dt_pac.date() == target_date:
                day_events.append((dt_pac, summary, raw, is_closed))

        # Sort by time (all-day first, then chronological)
        day_events.sort(key=lambda x: (1 if x[3] else 0, x[0]))

        # Print heading
        heading = target_date.strftime("%A, %B %d, %Y")
        print(f"\n{'=' * 50}")
        print(f"  {heading}")
        print(f"{'=' * 50}")

        if not day_events:
            print("  No events — appears open all day")
            continue

        for dt_pac, summary, raw, is_closed in day_events:
            if is_closed:
                print(f"  🚫 {summary} (all day)")
            elif "VALUE=DATE" in raw:
                print(f"  📅 {summary} (all day)")
            else:
                time_str = dt_pac.strftime("%I:%M %p").lstrip("0")
                print(f"  🎸 {time_str} — {summary}")

    print()


if __name__ == "__main__":
    main()
