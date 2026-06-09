#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date


MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

CITY_HINTS = [
    "Ventura",
    "Santa Barbara",
    "Goleta",
    "Pismo Beach",
    "Los Olivos",
    "Ojai",
    "Nipomo",
    "Westlake",
    "Calabasas",
]


def normalize_space(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip(" .,!?:;\n\t")


def extract_absolute_date(text: str, current_year: int) -> str | None:
    match = re.search(
        r"\b("
        + "|".join(MONTHS)
        + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    month = MONTHS[match.group(1).lower()]
    day = int(match.group(2))
    year = int(match.group(3) or current_year)
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def extract_time(text: str) -> str | None:
    match = re.search(r"\b(\d{1,2})(?::([0-5]\d))?\s*([ap]\.?m\.?)\b", text, flags=re.IGNORECASE)
    if not match:
        return None
    hour = str(int(match.group(1)))
    minute = f":{match.group(2)}" if match.group(2) else ""
    suffix = match.group(3).lower().replace(".", "")
    return f"{hour}{minute}{suffix}"


def extract_city(text: str) -> str | None:
    in_city = re.search(r"\bin\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)\b", text)
    if in_city:
        candidate = normalize_space(in_city.group(1))
        if candidate in CITY_HINTS:
            return candidate

    for city in CITY_HINTS:
        if re.search(rf"\b{re.escape(city)}\b", text, flags=re.IGNORECASE):
            return city
    return None


def extract_venue(text: str) -> str | None:
    patterns = [
        r"\bbook\s+(.+?)\s+(?:on|for)\s+(?:"
        + "|".join(MONTHS)
        + r"|\d{1,2}[/-]\d{1,2}|next|this)\b",
        r"\bbook\s+(.+?)\s+(?:at|@)\s+\d{1,2}",
        r"\bplaying\s+(?:at\s+)?(.+?)\s+(?:on|at|@)\s+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_space(match.group(1))
    return None


def has_relative_date(text: str) -> bool:
    return bool(re.search(r"\b(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text, re.I))


def build_acknowledgment_draft() -> str:
    return (
        "Thanks for reaching out. I am Neon V2, Neon Blonde's automated AI assistant. "
        "We received your booking request and are checking it now.\n\n"
        "Mike will review the date and I will follow up and confirm with you once "
        "everything has been checked. If there are any special notes, event details, "
        "load-in instructions, or other requests, feel free to send them over.\n\n"
        "- Neon V2"
    )


def parse_booking_request(email_text: str, current_year: int = 2026) -> dict:
    venue = extract_venue(email_text)
    parsed_date = extract_absolute_date(email_text, current_year)
    parsed_time = extract_time(email_text)
    city = extract_city(email_text)

    missing_fields = []
    if not venue:
        missing_fields.append("venue")
    if not parsed_date:
        missing_fields.append("date")
    if not parsed_time:
        missing_fields.append("time")
    if not city:
        missing_fields.append("city")

    review_flags = []
    if has_relative_date(email_text):
        review_flags.append("RELATIVE_DATE_REVIEW")

    status = "ready_for_mike_review" if not missing_fields else "needs_info"

    return {
        "status": status,
        "venue": venue,
        "date": parsed_date,
        "time": parsed_time,
        "city": city,
        "missing_fields": missing_fields,
        "review_flags": review_flags,
        "acknowledgment_draft": build_acknowledgment_draft(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a booking-request email into a Neon V2 intake receipt.")
    parser.add_argument("--text", help="Raw email text to parse.")
    parser.add_argument("--file", help="Path to a text file containing the raw email.")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            email_text = f.read()
    elif args.text:
        email_text = args.text
    else:
        parser.error("Provide --text or --file")

    print(json.dumps(parse_booking_request(email_text), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
