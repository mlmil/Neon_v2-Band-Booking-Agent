#!/usr/bin/env python3
"""
Neon V2 Venue Advertising Verifier

Checks venue public websites/calendars against the published Band Sheet
to verify that confirmed gigs are being advertised correctly by venues.

Result model (per worklog agreement):
- MATCH: venue advertising matches Band Sheet
- MISMATCH: venue advertising conflicts with Band Sheet (operational alert)
- GIG_NOT_ADVERTISED: venue does not list the gig (not an error)
- DATA_UNAVAILABLE: could not fetch venue data

Usage:
    python3 scripts/venue_advertising_verifier.py
    python3 scripts/venue_advertising_verifier.py --bandsheet-url URL --output json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bandsheet_verification_report import (
    BANDSHEET_JSON_URL,
    PACIFIC,
    _is_gig_like_title,
    _norm,
    _venues_match,
    fetch_json,
    filter_gigs_on_or_after,
    parse_bandsheet_json,
)


# ---------------------------------------------------------------------------
# Venue source adapters
# ---------------------------------------------------------------------------

class VenueSource:
    """Base class for venue advertising sources."""

    name: str = ""
    url: str = ""

    def fetch(self) -> str | None:
        """Fetch raw text/HTML from the venue source. Returns None on failure."""
        raise NotImplementedError

    def parse_events(self, raw: str) -> list[dict]:
        """Parse raw text into a list of {date, title, time?, url?} dicts."""
        raise NotImplementedError


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML to text extractor."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _html_to_text(raw_html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(raw_html)
    return html.unescape(parser.get_text())


def _fetch_url(url: str, timeout: int = 20) -> str | None:
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "NeonV2 VenueVerifier/1.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Tony's Pizzaria — Ventura, CA
# ---------------------------------------------------------------------------

class TonysPizzariaSource(VenueSource):
    """Tony's Pizzaria website events page."""

    name = "Tony's Pizzaria"
    url = "https://www.tonyspizzaria.com/events"

    def fetch(self) -> str | None:
        return _fetch_url(self.url)

    def parse_events(self, raw: str) -> list[dict]:
        text = _html_to_text(raw)
        events = []
        # Look for date-like patterns: "August 2", "Aug 16", "8/28", etc.
        # Tony's typically lists events with month + day
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
            "oct": 10, "nov": 11, "dec": 12,
        }
        current_year = datetime.now(PACIFIC).year

        # Pattern: Month Day (e.g., "August 2", "Sep 13")
        for match in re.finditer(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?\b",
            text,
            re.IGNORECASE,
        ):
            month_str, day_str, year_str = match.groups()
            month = month_map.get(month_str.lower())
            if not month:
                continue
            day = int(day_str)
            year = int(year_str) if year_str else current_year
            try:
                event_date = date(year, month, day)
            except ValueError:
                continue
            # Get surrounding context for title
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].strip()
            events.append({
                "date": event_date.isoformat(),
                "title": context,
                "source": self.name,
            })
        return events


# ---------------------------------------------------------------------------
# Leashless Brewing — Ventura, CA
# ---------------------------------------------------------------------------

class LeashlessBrewingSource(VenueSource):
    """Leashless Brewing website music events page.

    Note: Squarespace calendar blocks are JavaScript-rendered. The raw HTML
    contains a placeholder but no event dates. parse_events returns an empty
    list for JS-rendered pages, which results in GIG_NOT_ADVERTISED status.
    """

    name = "Leashless Brewing"
    url = "https://www.leashlessbrewing.com/music-events"

    def fetch(self) -> str | None:
        return _fetch_url(self.url)

    def parse_events(self, raw: str) -> list[dict]:
        # Squarespace calendar blocks are JavaScript-rendered.
        # The raw HTML contains a placeholder but no event dates.
        # Check for the calendar block marker to confirm the page loaded,
        # then return empty events (dates are not extractable from static HTML).
        if "sqs-block-calendar" in raw or 'data-block-type="26"' in raw:
            # Page loaded but events are rendered client-side via JS.
            # Return empty list — this will result in GIG_NOT_ADVERTISED
            # since no events can be found in the static HTML.
            return []
        # Fallback: try to parse any static dates (unlikely but harmless)
        text = _html_to_text(raw)
        events = []
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
            "oct": 10, "nov": 11, "dec": 12,
        }
        current_year = datetime.now(PACIFIC).year

        for match in re.finditer(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?\b",
            text,
            re.IGNORECASE,
        ):
            month_str, day_str, year_str = match.groups()
            month = month_map.get(month_str.lower())
            if not month:
                continue
            day = int(day_str)
            year = int(year_str) if year_str else current_year
            try:
                event_date = date(year, month, day)
            except ValueError:
                continue
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].strip()
            events.append({
                "date": event_date.isoformat(),
                "title": context,
                "source": self.name,
            })
        return events


# ---------------------------------------------------------------------------
# Figueroa Mountain Brewing — Santa Barbara, CA
# ---------------------------------------------------------------------------

class FigueroaMountainSource(VenueSource):
    """Figueroa Mountain Brewing website events page."""

    name = "Figueroa Mountain Brewing"
    url = "https://www.figmtnbrew.com/events"

    def fetch(self) -> str | None:
        return _fetch_url(self.url)

    def parse_events(self, raw: str) -> list[dict]:
        text = _html_to_text(raw)
        events = []
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
            "oct": 10, "nov": 11, "dec": 12,
        }
        current_year = datetime.now(PACIFIC).year

        for match in re.finditer(
            r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?\b",
            text,
            re.IGNORECASE,
        ):
            month_str, day_str, year_str = match.groups()
            month = month_map.get(month_str.lower())
            if not month:
                continue
            day = int(day_str)
            year = int(year_str) if year_str else current_year
            try:
                event_date = date(year, month, day)
            except ValueError:
                continue
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].strip()
            events.append({
                "date": event_date.isoformat(),
                "title": context,
                "source": self.name,
            })
        return events


# ---------------------------------------------------------------------------
# Verifier engine
# ---------------------------------------------------------------------------

VENUE_SOURCES: list[VenueSource] = [
    TonysPizzariaSource(),
    LeashlessBrewingSource(),
    FigueroaMountainSource(),
]

# Map venue names from Band Sheet to source names for matching
VENUE_NAME_ALIASES: dict[str, str] = {
    "tonys pizzaria": "Tony's Pizzaria",
    "tony's pizzaria": "Tony's Pizzaria",
    "tonys pizza": "Tony's Pizzaria",
    "tony's pizza": "Tony's Pizzaria",
    "leashless brewing": "Leashless Brewing",
    "leashless": "Leashless Brewing",
    "figueroa mountain brewing": "Figueroa Mountain Brewing",
    "figueroa mountain": "Figueroa Mountain Brewing",
    "fig mountain": "Figueroa Mountain Brewing",
    "fig mtn": "Figueroa Mountain Brewing",
}


def _find_venue_source(bandsheet_venue: str) -> VenueSource | None:
    """Find the matching venue source for a Band Sheet venue name."""
    norm = _norm(bandsheet_venue)
    for alias, source_name in VENUE_NAME_ALIASES.items():
        if _norm(alias) in norm or norm in _norm(alias):
            for src in VENUE_SOURCES:
                if src.name == source_name:
                    return src
    return None


def _gig_matches_event(gig: dict, event: dict) -> bool:
    """Check if a Band Sheet gig matches a venue-advertised event."""
    if gig["date"] != event["date"]:
        return False
    # Check if the event title mentions the band or venue
    event_title = event.get("title", "").lower()
    band_keywords = ["neon blonde", "neonblonde", "80s", "cover band"]
    return any(kw in event_title for kw in band_keywords)


def verify_venue_advertising(
    bandsheet_gigs: list[dict],
    *,
    lookback_days: int = 7,
    lookahead_days: int = 90,
) -> dict:
    """
    Compare Band Sheet gigs against venue-advertised events.

    Returns a dict with per-gig verification results.
    """
    today = datetime.now(PACIFIC).date()
    window_start = today - timedelta(days=lookback_days)
    window_end = today + timedelta(days=lookahead_days)

    # Filter gigs to the verification window
    gigs_in_window = [
        g for g in bandsheet_gigs
        if window_start <= date.fromisoformat(g["date"]) <= window_end
    ]

    results = []
    alerts = []

    for gig in gigs_in_window:
        source = _find_venue_source(gig["venue"])
        if source is None:
            # No adapter for this venue — skip
            results.append({
                "gig": gig,
                "status": "NO_ADAPTER",
                "detail": f"No venue source adapter for '{gig['venue']}'",
            })
            continue

        raw = source.fetch()
        if raw is None:
            results.append({
                "gig": gig,
                "status": "DATA_UNAVAILABLE",
                "detail": f"Could not fetch {source.url}",
                "venue_source": source.name,
            })
            continue

        events = source.parse_events(raw)
        matching_events = [e for e in events if _gig_matches_event(gig, e)]

        if not matching_events:
            # Check if the venue has any events on this date at all
            same_date_events = [e for e in events if e["date"] == gig["date"]]
            if same_date_events:
                # Venue has events on this date but none mention Neon Blonde
                results.append({
                    "gig": gig,
                    "status": "MISMATCH",
                    "detail": f"Venue has {len(same_date_events)} event(s) on {gig['date']} but none mention Neon Blonde",
                    "venue_source": source.name,
                    "venue_events_on_date": same_date_events,
                })
                alerts.append({
                    "type": "MISMATCH",
                    "gig": gig,
                    "venue_source": source.name,
                    "detail": f"Venue advertising conflicts with Band Sheet for {gig['date']}",
                })
            else:
                results.append({
                    "gig": gig,
                    "status": "GIG_NOT_ADVERTISED",
                    "detail": f"No events found on {gig['date']} at {source.name}",
                    "venue_source": source.name,
                })
        else:
            # Check if details match (time, etc.)
            best_match = matching_events[0]
            mismatch_details = []
            # Compare time if available in both
            if gig.get("time") and best_match.get("time"):
                if _norm(gig["time"]) != _norm(best_match["time"]):
                    mismatch_details.append(
                        f"time: Band Sheet={gig['time']} vs venue={best_match['time']}"
                    )
            if mismatch_details:
                results.append({
                    "gig": gig,
                    "status": "MISMATCH",
                    "detail": "; ".join(mismatch_details),
                    "venue_source": source.name,
                    "venue_event": best_match,
                })
                alerts.append({
                    "type": "MISMATCH",
                    "gig": gig,
                    "venue_source": source.name,
                    "detail": "; ".join(mismatch_details),
                })
            else:
                results.append({
                    "gig": gig,
                    "status": "MATCH",
                    "detail": f"Venue advertising matches Band Sheet",
                    "venue_source": source.name,
                    "venue_event": best_match,
                })

    return {
        "status": "alert" if alerts else "ok",
        "alerts": alerts,
        "results": results,
        "checked_at": datetime.now(PACIFIC).isoformat(),
        "window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
        },
    }


def run_live_check(
    *,
    bandsheet_url: str = BANDSHEET_JSON_URL,
    lookback_days: int = 7,
    lookahead_days: int = 90,
) -> dict:
    """Fetch Band Sheet and run venue advertising verification."""
    bandsheet_data = fetch_json(bandsheet_url)
    today = datetime.now(PACIFIC).date()
    bandsheet_gigs = filter_gigs_on_or_after(
        parse_bandsheet_json(bandsheet_data),
        today - timedelta(days=lookback_days),
    )
    return verify_venue_advertising(
        bandsheet_gigs,
        lookback_days=lookback_days,
        lookahead_days=lookahead_days,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify venue advertising against the published Band Sheet."
    )
    parser.add_argument("--bandsheet-url", default=BANDSHEET_JSON_URL)
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--lookahead-days", type=int, default=90)
    parser.add_argument("--output", choices=["json", "text"], default="json")
    args = parser.parse_args()

    result = run_live_check(
        bandsheet_url=args.bandsheet_url,
        lookback_days=args.lookback_days,
        lookahead_days=args.lookahead_days,
    )

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Venue Advertising Verification — {result['checked_at']}")
        print(f"Window: {result['window']['start']} to {result['window']['end']}")
        print(f"Overall: {result['status'].upper()}")
        print()
        for r in result["results"]:
            gig = r["gig"]
            status = r["status"]
            print(f"  {gig['date']} @ {gig['venue']} ({gig.get('city', '?')})")
            print(f"    Status: {status}")
            if r.get("detail"):
                print(f"    Detail: {r['detail']}")
            if r.get("venue_source"):
                print(f"    Source: {r['venue_source']}")
            print()
        if result["alerts"]:
            print("ALERTS:")
            for a in result["alerts"]:
                print(f"  [{a['type']}] {a['gig']['date']} @ {a['gig']['venue']}: {a['detail']}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
