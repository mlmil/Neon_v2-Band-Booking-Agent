#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


VENUES_ROOT = Path("/Volumes/VADER/Manifold/Neon_Blonde/Venues")
TEST_VENUE_ALIASES = {"club babaloo", "club bobaloo"}
TEST_VENUE_FOLDER = "_Test Venues"
SANTA_BARBARA_AREA_CITIES = {"santa barbara", "goleta", "carpinteria", "montecito"}


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    location: str
    start: str


def normalize_venue_name(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9 ]+", "", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def is_test_venue(value: str) -> bool:
    return normalize_venue_name(value) in TEST_VENUE_ALIASES


def _date_from_start(start: str) -> str:
    return datetime.fromisoformat(start.replace("Z", "+00:00")).date().isoformat()


def _warnings_for_event(event: CalendarEvent) -> list[dict]:
    start = event.start
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    warnings = []
    if start_dt.weekday() <= 3:
        warnings.append(
            {
                "code": "WEEKDAY_GIG_REVIEW",
                "message": "Weekday gig; Neon Blonde rarely plays Monday-Thursday.",
            }
        )
    city = normalize_venue_name(event.location)
    if city in SANTA_BARBARA_AREA_CITIES and start_dt.weekday() <= 4 and start_dt.hour <= 19:
        warnings.append(
            {
                "code": "SB_EARLY_WEEKDAY_LOGISTICS",
                "message": (
                    "Early Santa Barbara-area weekday gig; Kyle works in Calabasas and Dave is in West Hills."
                ),
            }
        )
    return warnings


def validate_calendar_event(event: CalendarEvent) -> dict:
    if not event.title.strip():
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Missing venue title"}
    if not event.location.strip():
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Missing city location"}
    if "," in event.location or "california" in event.location.lower() or "united states" in event.location.lower():
        return {
            "status": "blocked",
            "code": "BLOCKED_CALENDAR",
            "failure_reason": "Location must be city only",
        }
    try:
        _date_from_start(event.start)
    except ValueError:
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Invalid start datetime"}
    return {"status": "success"}


def _resolve_venue_folder(venue_name: str, venues_root: Path) -> Path | None:
    target = normalize_venue_name(venue_name)
    for child in venues_root.iterdir() if venues_root.exists() else []:
        if child.is_dir() and normalize_venue_name(child.name) == target:
            return child
    return None


def build_folder_plan(event: CalendarEvent, venues_root: Path = VENUES_ROOT) -> dict:
    validation = validate_calendar_event(event)
    if validation["status"] != "success":
        return validation
    if is_test_venue(event.title):
        venue_folder = venues_root / TEST_VENUE_FOLDER / "Club Babaloo"
        gig_date = _date_from_start(event.start)
        return {
            "status": "success",
            "code": "TEST_VENUE",
            "is_test_venue": True,
            "warnings": _warnings_for_event(event),
            "venue_folder": str(venue_folder),
            "gig_folder": str(venue_folder / "gigs" / gig_date),
            "reconciliation_path": str(venue_folder / "gigs" / gig_date / "RECONCILIATION.md"),
        }
    venue_folder = _resolve_venue_folder(event.title, venues_root)
    if venue_folder is None:
        venue_folder = venues_root / re.sub(r"[/:\"]+", "", event.title).strip()
        status = "needs_review"
        code = "NEEDS_VENUE_REVIEW"
    else:
        status = "success"
        code = "VENUE_RESOLVED"
    gig_date = _date_from_start(event.start)
    return {
        "status": status,
        "code": code,
        "warnings": _warnings_for_event(event),
        "venue_folder": str(venue_folder),
        "gig_folder": str(venue_folder / "gigs" / gig_date),
        "reconciliation_path": str(venue_folder / "gigs" / gig_date / "RECONCILIATION.md"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--venues-root", default=str(VENUES_ROOT))
    args = parser.parse_args()
    event = CalendarEvent(args.title, args.location, args.start)
    print(json.dumps(build_folder_plan(event, Path(args.venues_root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
