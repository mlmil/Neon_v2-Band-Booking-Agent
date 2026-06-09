#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bandsheet_verification_report import (
    BANDSHEET_JSON_URL,
    PACIFIC,
    _is_gig_like_title,
    _venues_match,
    fetch_json,
    filter_gigs_on_or_after,
    parse_bandsheet_json,
)
from scripts.venue_agent_tool import is_test_venue


WORDPRESS_SHOWS_URL = (
    "https://neonblonde.band/wp-json/wp/v2/show"
    "?per_page=100&status=publish&_fields=id,title,link,featured_media,show_year,menu_order"
)
DEFAULT_USER_AGENT = "NeonV2 Website Sync"
MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _clean_title(value: str) -> str:
    return html.unescape(value).replace("–", "-").replace("—", "-").strip()


def parse_wordpress_show(post: dict, *, year: int = 2026) -> dict | None:
    title = _clean_title(post.get("title", {}).get("rendered", ""))
    match = re.match(
        r"^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})\s+(.+)$",
        title,
        re.IGNORECASE,
    )
    if not match:
        return None
    month_name, day, venue = match.groups()
    show_date = date(year, MONTHS[month_name.lower()], int(day))
    return {
        "date": show_date.isoformat(),
        "venue": venue.strip(),
        "id": post.get("id"),
        "title": title,
        "link": post.get("link"),
    }


def parse_wordpress_shows(posts: list[dict], *, year: int = 2026) -> list[dict]:
    shows = []
    for post in posts:
        show = parse_wordpress_show(post, year=year)
        if show is not None and _is_gig_like_title(show["venue"]):
            shows.append(show)
    return sorted(shows, key=lambda show: (show["date"], show["venue"]))


def add_cache_buster(url: str, *, token: str | None = None) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_cb={token or int(time.time())}"


def _public_venues_match(bandsheet_venue: str, website_venue: str) -> bool:
    if _venues_match(bandsheet_venue, website_venue):
        return True
    bandsheet_norm = re.sub(r"[^a-z0-9]+", " ", bandsheet_venue.lower()).strip()
    website_norm = re.sub(r"[^a-z0-9]+", " ", website_venue.lower()).strip()
    return bandsheet_norm.startswith("private party") and website_norm in {"private gig", "private show", "private party"}


def compare_website_to_bandsheet(bandsheet_gigs: list[dict], website_shows: list[dict]) -> dict:
    mismatches = []
    matched_website_indexes = set()

    for bandsheet_gig in bandsheet_gigs:
        same_date = [
            (index, website_show)
            for index, website_show in enumerate(website_shows)
            if website_show["date"] == bandsheet_gig["date"]
        ]
        match = next(
            (
                (index, website_show)
                for index, website_show in same_date
                if index not in matched_website_indexes
                and _public_venues_match(bandsheet_gig["venue"], website_show["venue"])
            ),
            None,
        )
        if match is None:
            mismatches.append(
                {
                    "type": "bandsheet_missing_or_different_on_website",
                    "bandsheet": bandsheet_gig,
                    "website_same_date": [website_show for _, website_show in same_date],
                }
            )
            continue
        matched_website_indexes.add(match[0])

    for index, website_show in enumerate(website_shows):
        if index in matched_website_indexes:
            continue
        mismatches.append(
            {
                "type": "website_missing_or_different_from_bandsheet",
                "website": website_show,
                "bandsheet_same_date": [
                    bandsheet_gig for bandsheet_gig in bandsheet_gigs if bandsheet_gig["date"] == website_show["date"]
                ],
            }
        )

    if mismatches:
        return {"status": "blocked", "code": "WEBSITE_MISMATCH", "mismatches": mismatches}
    return {"status": "success", "mismatches": []}


def fetch_wordpress_shows(url: str = WORDPRESS_SHOWS_URL) -> list[dict]:
    req = urllib.request.Request(
        add_cache_buster(url),
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_live_check(
    *,
    bandsheet_url: str = BANDSHEET_JSON_URL,
    wordpress_url: str = WORDPRESS_SHOWS_URL,
) -> dict:
    bandsheet_data = fetch_json(bandsheet_url)
    posts = fetch_wordpress_shows(wordpress_url)
    today = datetime.now(PACIFIC).date()
    bandsheet_gigs = filter_gigs_on_or_after(parse_bandsheet_json(bandsheet_data), today)
    bandsheet_gigs = [
        gig for gig in bandsheet_gigs if _is_gig_like_title(gig["venue"]) and not is_test_venue(gig["venue"])
    ]
    website_shows = filter_gigs_on_or_after(parse_wordpress_shows(posts), today)
    result = compare_website_to_bandsheet(bandsheet_gigs, website_shows)
    return {
        **result,
        "bandsheet_updated": bandsheet_data.get("updated"),
        "bandsheet_count": len(bandsheet_gigs),
        "website_count": len(website_shows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare published Band Sheet gigs against WordPress public show posts.")
    parser.add_argument("--bandsheet-url", default=BANDSHEET_JSON_URL)
    parser.add_argument("--wordpress-url", default=WORDPRESS_SHOWS_URL)
    args = parser.parse_args()
    print(json.dumps(run_live_check(bandsheet_url=args.bandsheet_url, wordpress_url=args.wordpress_url), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
