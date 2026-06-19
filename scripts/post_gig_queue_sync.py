#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.bandsheet_verification_report import PUBLIC_CALENDAR_ICS_URL
from scripts.local_venue_folder_sync import clean_calendar_venue_title


PACIFIC = ZoneInfo("America/Los_Angeles")
DEFAULT_QUEUE = Path("data/post_gig/queue.csv")
FIELDNAMES = [
    "gig_id",
    "venue",
    "city",
    "date",
    "start_at",
    "end_at",
    "queue_status",
    "next_step",
    "created_at",
    "updated_at",
]
PROTECTED_STATUSES = {"closed"}


@dataclass(frozen=True)
class QueueGig:
    gig_id: str
    venue: str
    city: str
    start_at: str
    end_at: str


def _unfold_ics(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").split("\n")
    unfolded = []
    for line in lines:
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _parse_ics_datetime(value: str, params: str = "") -> datetime | None:
    if "VALUE=DATE" in params or "T" not in value:
        return None
    if value.endswith("Z"):
        parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return parsed.astimezone(PACIFIC)
    parsed = datetime.strptime(value, "%Y%m%dT%H%M%S")
    tz_match = re.search(r"TZID=([^;:]+)", params)
    timezone_name = tz_match.group(1) if tz_match else "America/Los_Angeles"
    try:
        source_timezone = ZoneInfo(timezone_name)
    except Exception:
        source_timezone = PACIFIC
    return parsed.replace(tzinfo=source_timezone).astimezone(PACIFIC)


def parse_calendar_queue_gigs(ics_text: str) -> list[QueueGig]:
    events = []
    current = None
    for line in _unfold_ics(ics_text):
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key_with_params, value = line.split(":", 1)
        key, _, params = key_with_params.partition(";")
        current[key] = value.replace("\\,", ",").strip()
        if params:
            current[f"{key}_PARAMS"] = params

    gigs = []
    for event in events:
        start = _parse_ics_datetime(event.get("DTSTART", ""), event.get("DTSTART_PARAMS", ""))
        end = _parse_ics_datetime(event.get("DTEND", ""), event.get("DTEND_PARAMS", ""))
        venue = clean_calendar_venue_title(event.get("SUMMARY", ""))
        city = event.get("LOCATION", "").strip()
        if not start or not city or not venue:
            continue
        if end is None or end <= start:
            end = start + timedelta(hours=3)
        gig_id = event.get("UID", "").strip() or f"{venue.lower()}-{start.date().isoformat()}"
        gigs.append(
            QueueGig(
                gig_id=gig_id,
                venue=venue,
                city=city,
                start_at=start.isoformat(),
                end_at=end.isoformat(),
            )
        )
    return gigs


def build_queue_row(gig: QueueGig, *, now: datetime | None = None) -> dict[str, str]:
    current_time = now or datetime.now(PACIFIC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=PACIFIC)
    end_at = datetime.fromisoformat(gig.end_at)
    if end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=PACIFIC)

    if current_time >= end_at:
        status = "needs_closeout"
        next_step = "Ask Mike for base pay received, tip jar, Venmo, payment method, recipient, and amount still owed."
    else:
        status = "scheduled"
        next_step = "Wait until the show ends."

    timestamp = current_time.isoformat()
    return {
        "gig_id": gig.gig_id,
        "venue": gig.venue,
        "city": gig.city,
        "date": datetime.fromisoformat(gig.start_at).date().isoformat(),
        "start_at": gig.start_at,
        "end_at": gig.end_at,
        "queue_status": status,
        "next_step": next_step,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def sync_queue(
    gigs: list[QueueGig],
    queue_path: str | Path = DEFAULT_QUEUE,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    path = Path(queue_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))
    existing_by_id = {row["gig_id"]: row for row in existing_rows}

    created = 0
    updated = 0
    activated = 0
    output_rows = []
    seen_ids = set()
    for gig in gigs:
        row = build_queue_row(gig, now=now)
        existing = existing_by_id.get(gig.gig_id)
        if existing:
            row["created_at"] = existing.get("created_at") or row["created_at"]
            if existing.get("queue_status") in PROTECTED_STATUSES:
                row["queue_status"] = existing["queue_status"]
                row["next_step"] = existing.get("next_step") or "No action."
            elif (
                row["queue_status"] == "needs_closeout"
                and existing.get("queue_status") != "needs_closeout"
            ):
                activated += 1
            updated += 1
        else:
            created += 1
            if row["queue_status"] == "needs_closeout":
                activated += 1
        output_rows.append(row)
        seen_ids.add(gig.gig_id)

    for existing in existing_rows:
        if existing.get("gig_id") not in seen_ids:
            output_rows.append(existing)

    output_rows.sort(key=lambda row: (row.get("start_at", ""), row.get("venue", "")))
    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
        temp_name = handle.name
    os.replace(temp_name, path)

    active = sum(row.get("queue_status") == "needs_closeout" for row in output_rows)
    scheduled = sum(row.get("queue_status") == "scheduled" for row in output_rows)
    return {
        "status": "success",
        "queue": str(path),
        "created": created,
        "updated": updated,
        "activated": activated,
        "active_closeouts": active,
        "scheduled": scheduled,
        "total": len(output_rows),
    }


def fetch_calendar_queue_gigs(calendar_url: str = PUBLIC_CALENDAR_ICS_URL) -> list[QueueGig]:
    request = urllib.request.Request(calendar_url, headers={"User-Agent": "NeonV2 Post-Gig Queue"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return parse_calendar_queue_gigs(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync the supervised Neon V2 Post-Gig queue.")
    parser.add_argument("--calendar-url", default=PUBLIC_CALENDAR_ICS_URL)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Include shows that ended within this many days; future shows are always included.",
    )
    args = parser.parse_args()

    now = datetime.now(PACIFIC)
    cutoff = now - timedelta(days=max(args.lookback_days, 0))
    try:
        gigs = fetch_calendar_queue_gigs(args.calendar_url)
        relevant = [gig for gig in gigs if datetime.fromisoformat(gig.end_at) >= cutoff]
        receipt = sync_queue(relevant, args.queue, now=now)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2))
        return 2

    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
