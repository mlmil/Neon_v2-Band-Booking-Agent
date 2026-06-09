#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import date, datetime
from zoneinfo import ZoneInfo


BANDSHEET_JSON_URL = "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/bandsheet-data.json"
PUBLIC_CALENDAR_ICS_URL = "https://calendar.google.com/calendar/ical/neonblondevc%40gmail.com/public/basic.ics"
PACIFIC = ZoneInfo("America/Los_Angeles")
NON_GIG_TITLE_PATTERNS = (
    " out",
    "out ",
    "rehearsal",
    "practice",
    "promo",
    "flyer",
    "automation",
    "meeting",
)


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _key(gig: dict) -> tuple[str, str]:
    return gig["date"], _norm(gig["venue"])


def _venues_match(left: str, right: str) -> bool:
    left_norm = _norm(left)
    right_norm = _norm(right)
    if left_norm == right_norm:
        return True
    if min(len(left_norm), len(right_norm)) < 6:
        return False
    return left_norm in right_norm or right_norm in left_norm


def _format_time(dt: datetime) -> str:
    hour = dt.hour
    minute = dt.minute
    suffix = "am" if hour < 12 else "pm"
    display_hour = hour % 12 or 12
    if minute:
        return f"{display_hour}:{minute:02d}{suffix}"
    return f"{display_hour}{suffix}"


def _clean_ics_value(value: str) -> str:
    return (
        value.replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\n", " ")
        .replace("\\N", " ")
        .strip()
    )


def _is_gig_like_title(title: str) -> bool:
    normalized = f" {title.lower().strip()} "
    return not any(pattern in normalized for pattern in NON_GIG_TITLE_PATTERNS)


def parse_bandsheet_gig(entry: str) -> dict:
    pattern = re.compile(
        r"^[A-Z]{3}\s+(\d{1,2})-(\d{1,2})-(\d{4})\s+@(\d{1,2})(?::(\d{2}))?\s*([AP]M)\s+—\s+(.+?),\s*([^,]+)\s*$"
    )
    match = pattern.match(entry.strip())
    if not match:
        raise ValueError(f"Could not parse Band Sheet gig: {entry}")
    month, day, year, hour, minute, suffix, venue, city = match.groups()
    hour_int = int(hour)
    minute_display = f":{minute}" if minute else ""
    return {
        "date": f"{int(year):04d}-{int(month):02d}-{int(day):02d}",
        "venue": venue.strip(),
        "city": city.strip(),
        "time": f"{hour_int}{minute_display}{suffix.lower()}",
    }


def parse_bandsheet_json(data: dict) -> list[dict]:
    gigs = []
    for entry in data.get("booked_gigs", []):
        try:
            gig = parse_bandsheet_gig(entry)
        except ValueError:
            continue
        if _is_gig_like_title(gig["venue"]):
            gigs.append(gig)
    return gigs


def _unfold_ics_lines(ics_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in ics_text.replace("\r\n", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        elif raw_line:
            lines.append(raw_line)
    return lines


def _parse_ics_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(PACIFIC)
    if "T" in value:
        return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=PACIFIC)
    return datetime.strptime(value, "%Y%m%d").replace(tzinfo=PACIFIC)


def _event_to_gig(event: dict) -> dict | None:
    title = _clean_ics_value(event.get("SUMMARY", ""))
    if not title or not _is_gig_like_title(title):
        return None
    start_raw = event.get("DTSTART")
    location = _clean_ics_value(event.get("LOCATION", ""))
    if not start_raw or not location or "VALUE=DATE" in event.get("DTSTART_PARAMS", ""):
        return None
    start = _parse_ics_datetime(start_raw)
    city = location.split(",")[-1].strip() if "," in location else location
    return {
        "date": start.date().isoformat(),
        "venue": title.strip(),
        "city": city,
        "time": _format_time(start),
    }


def parse_calendar_ics(ics_text: str) -> list[dict]:
    events = []
    current: dict | None = None
    for line in _unfold_ics_lines(ics_text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None:
                gig = _event_to_gig(current)
                if gig is not None:
                    events.append(gig)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        name_part, value = line.split(":", 1)
        name_bits = name_part.split(";")
        name = name_bits[0]
        current[name] = value
        if len(name_bits) > 1:
            current[f"{name}_PARAMS"] = ";".join(name_bits[1:])
    return sorted(events, key=lambda gig: (gig["date"], gig["venue"]))


def compare_gigs(calendar_gigs: list[dict], bandsheet_gigs: list[dict]) -> dict:
    mismatches = []
    matched_bandsheet_indexes = set()

    for gig in calendar_gigs:
        match_index = next(
            (
                index
                for index, bandsheet_gig in enumerate(bandsheet_gigs)
                if index not in matched_bandsheet_indexes
                and gig["date"] == bandsheet_gig["date"]
                and _venues_match(gig["venue"], bandsheet_gig["venue"])
            ),
            None,
        )
        if match_index is None:
            mismatches.append({"type": "calendar_missing_from_bandsheet", "gig": gig})
            continue
        matched_bandsheet_indexes.add(match_index)
        other = bandsheet_gigs[match_index]
        for field in ["city", "time"]:
            if _norm(str(gig.get(field, ""))) != _norm(str(other.get(field, ""))):
                mismatches.append({"type": f"{field}_mismatch", "calendar": gig, "bandsheet": other})

    for index, gig in enumerate(bandsheet_gigs):
        if index not in matched_bandsheet_indexes:
            mismatches.append({"type": "bandsheet_missing_from_calendar", "gig": gig})

    if mismatches:
        return {"status": "blocked", "code": "BANDSHEET_MISMATCH", "mismatches": mismatches}
    return {"status": "success", "mismatches": []}


def filter_gigs_on_or_after(gigs: list[dict], start_date: date) -> list[dict]:
    return [gig for gig in gigs if date.fromisoformat(gig["date"]) >= start_date]


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("utf-8")


def run_live_check(
    *,
    bandsheet_url: str = BANDSHEET_JSON_URL,
    calendar_url: str = PUBLIC_CALENDAR_ICS_URL,
) -> dict:
    bandsheet_data = fetch_json(bandsheet_url)
    calendar_ics = fetch_text(calendar_url)
    today = datetime.now(PACIFIC).date()
    calendar_gigs = filter_gigs_on_or_after(parse_calendar_ics(calendar_ics), today)
    bandsheet_gigs = filter_gigs_on_or_after(parse_bandsheet_json(bandsheet_data), today)
    result = compare_gigs(calendar_gigs, bandsheet_gigs)
    return {
        **result,
        "bandsheet_updated": bandsheet_data.get("updated"),
        "calendar_count": len(calendar_gigs),
        "bandsheet_count": len(bandsheet_gigs),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare published Band Sheet gigs against public Google Calendar.")
    parser.add_argument("--bandsheet-url", default=BANDSHEET_JSON_URL)
    parser.add_argument("--calendar-url", default=PUBLIC_CALENDAR_ICS_URL)
    args = parser.parse_args()
    print(json.dumps(run_live_check(bandsheet_url=args.bandsheet_url, calendar_url=args.calendar_url), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
