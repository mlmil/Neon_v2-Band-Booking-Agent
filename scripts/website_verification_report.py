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
from html.parser import HTMLParser
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
WORDPRESS_HOME_URL = "https://neonblonde.band/"
HOSTED_WIDGET_MARKER = "public-shows-widget.html"
HOSTED_WIDGET_DATA_MARKER = "bandsheet-data.json"
HOSTED_WIDGET_DISPLAY_LIMIT = 8
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


class _ShowTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._capture: str | None = None
        self.tokens: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        class_value = next((value for name, value in attrs if name == "class"), "") or ""
        classes = set(class_value.split())
        if "x-text-content-text-primary" in classes:
            self._capture = "primary"
        elif "x-text-content-text-subheadline" in classes:
            self._capture = "subheadline"

    def handle_endtag(self, tag: str) -> None:
        if self._capture is not None:
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._capture is None:
            return
        text = _clean_title(data)
        if text:
            self.tokens.append((self._capture, text))


class _IframeSrcParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "iframe":
            return
        src = next((value for name, value in attrs if name.lower() == "src"), None)
        if src:
            self.srcs.append(html.unescape(src))


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


def parse_rendered_show_date(value: str, *, year: int = 2026) -> str | None:
    match = re.match(
        r"^(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})$",
        value,
        re.IGNORECASE,
    )
    if not match:
        return None
    month_name, day = match.groups()
    return date(year, MONTHS[month_name.lower()], int(day)).isoformat()


def parse_rendered_show_subheadline(value: str) -> tuple[str | None, str | None]:
    match = re.match(r"^\s*([0-9]{1,2}(?::[0-9]{2})?\s*[ap]m)\s*-\s*(.+?)\s*$", value, re.IGNORECASE)
    if not match:
        return None, None
    time_value, city = match.groups()
    return time_value.lower().replace(" ", ""), city.strip()


def parse_rendered_show_cards(page_html: str, *, year: int = 2026) -> list[dict]:
    lower_html = page_html.lower()
    start = lower_html.find("upcoming shows")
    if start == -1:
        return []
    end = lower_html.find("now booking", start)
    section_html = page_html[start:end if end != -1 else len(page_html)]

    parser = _ShowTextParser()
    parser.feed(section_html)

    shows = []
    index = 0
    while index < len(parser.tokens):
        kind, text = parser.tokens[index]
        show_date = parse_rendered_show_date(text, year=year) if kind == "primary" else None
        if show_date is None:
            index += 1
            continue
        if index + 2 >= len(parser.tokens):
            break
        venue_kind, venue = parser.tokens[index + 1]
        detail_kind, detail = parser.tokens[index + 2]
        if venue_kind != "primary" or detail_kind != "subheadline":
            index += 1
            continue
        time_value, city = parse_rendered_show_subheadline(detail)
        if time_value is None:
            index += 1
            continue
        shows.append(
            {
                "date": show_date,
                "venue": venue,
                "city": city,
                "time": time_value,
                "title": f"{text} {venue}",
                "source": "rendered_page",
            }
        )
        index += 3
    return sorted(shows, key=lambda show: (show["date"], show["venue"]))


def find_hosted_widget_src(page_html: str) -> str | None:
    parser = _IframeSrcParser()
    parser.feed(page_html)
    return next((src for src in parser.srcs if HOSTED_WIDGET_MARKER in src), None)


def add_cache_buster(url: str, *, token: str | None = None) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_cb={token or int(time.time())}"


def _public_venues_match(bandsheet_venue: str, website_venue: str) -> bool:
    if _venues_match(bandsheet_venue, website_venue):
        return True
    bandsheet_norm = re.sub(r"[^a-z0-9]+", " ", bandsheet_venue.lower()).strip()
    website_norm = re.sub(r"[^a-z0-9]+", " ", website_venue.lower()).strip()
    return bandsheet_norm.startswith("private party") and website_norm in {"private gig", "private show", "private party"}


def _public_field_matches(field: str, bandsheet_value: str, website_value: str) -> bool:
    left = re.sub(r"[^a-z0-9]+", "", bandsheet_value.lower())
    right = re.sub(r"[^a-z0-9]+", "", website_value.lower())
    if left == right:
        return True
    if field == "city" and len(left) >= 4:
        return right.startswith(left)
    return False


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
        website_show = match[1]
        for field in ["city", "time"]:
            if field not in website_show or field not in bandsheet_gig:
                continue
            if not _public_field_matches(field, str(bandsheet_gig[field]), str(website_show[field])):
                mismatches.append(
                    {
                        "type": f"{field}_mismatch",
                        "bandsheet": bandsheet_gig,
                        "website": website_show,
                    }
                )

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


def fetch_rendered_page(url: str = WORDPRESS_HOME_URL) -> str:
    req = urllib.request.Request(
        add_cache_buster(url),
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_text_url(url: str) -> str:
    req = urllib.request.Request(
        add_cache_buster(url),
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def verify_hosted_widget(page_html: str) -> dict:
    widget_src = find_hosted_widget_src(page_html)
    if widget_src is None:
        return {
            "status": "blocked",
            "code": "HOSTED_WIDGET_MISSING",
            "mismatches": [{"type": "hosted_widget_missing"}],
        }
    widget_html = fetch_text_url(widget_src)
    if HOSTED_WIDGET_DATA_MARKER not in widget_html:
        return {
            "status": "blocked",
            "code": "HOSTED_WIDGET_DATA_SOURCE_MISSING",
            "widget_src": widget_src,
            "mismatches": [{"type": "hosted_widget_data_source_missing"}],
        }
    return {
        "status": "success",
        "mismatches": [],
        "widget_src": widget_src,
        "display_limit": HOSTED_WIDGET_DISPLAY_LIMIT,
    }


def run_live_check(
    *,
    bandsheet_url: str = BANDSHEET_JSON_URL,
    wordpress_url: str = WORDPRESS_SHOWS_URL,
    rendered_page_url: str = WORDPRESS_HOME_URL,
) -> dict:
    bandsheet_data = fetch_json(bandsheet_url)
    posts = fetch_wordpress_shows(wordpress_url)
    rendered_page = fetch_rendered_page(rendered_page_url)
    today = datetime.now(PACIFIC).date()
    bandsheet_gigs = filter_gigs_on_or_after(parse_bandsheet_json(bandsheet_data), today)
    bandsheet_gigs = [
        gig for gig in bandsheet_gigs if _is_gig_like_title(gig["venue"]) and not is_test_venue(gig["venue"])
    ]
    website_shows = filter_gigs_on_or_after(parse_wordpress_shows(posts), today)
    rendered_shows = filter_gigs_on_or_after(parse_rendered_show_cards(rendered_page), today)
    posts_result = compare_website_to_bandsheet(bandsheet_gigs, website_shows)
    hosted_widget_src = find_hosted_widget_src(rendered_page)
    if hosted_widget_src is not None:
        rendered_result = verify_hosted_widget(rendered_page)
        rendered_count = min(HOSTED_WIDGET_DISPLAY_LIMIT, len(bandsheet_gigs))
    else:
        rendered_result = compare_website_to_bandsheet(bandsheet_gigs, rendered_shows)
        rendered_count = len(rendered_shows)
    checks = {
        "wordpress_posts_advisory": posts_result,
        "rendered_page": rendered_result,
    }
    mismatch_sources = {
        name: result
        for name, result in checks.items()
        if result.get("status") != "success" and name != "wordpress_posts_advisory"
    }
    result = (
        {"status": "blocked", "code": "WEBSITE_MISMATCH", "checks": checks}
        if mismatch_sources
        else {"status": "success", "mismatches": [], "checks": checks}
    )
    all_mismatches = []
    for source, check in mismatch_sources.items():
        for mismatch in check.get("mismatches", []):
            all_mismatches.append({"source": source, **mismatch})
    return {
        **result,
        "mismatches": all_mismatches,
        "bandsheet_updated": bandsheet_data.get("updated"),
        "bandsheet_count": len(bandsheet_gigs),
        "website_count": len(website_shows),
        "rendered_count": rendered_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare published Band Sheet gigs against WordPress public show posts.")
    parser.add_argument("--bandsheet-url", default=BANDSHEET_JSON_URL)
    parser.add_argument("--wordpress-url", default=WORDPRESS_SHOWS_URL)
    parser.add_argument("--rendered-page-url", default=WORDPRESS_HOME_URL)
    args = parser.parse_args()
    print(
        json.dumps(
            run_live_check(
                bandsheet_url=args.bandsheet_url,
                wordpress_url=args.wordpress_url,
                rendered_page_url=args.rendered_page_url,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
