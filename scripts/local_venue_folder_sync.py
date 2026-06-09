#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.bandsheet_verification_report import PUBLIC_CALENDAR_ICS_URL, parse_calendar_ics
from scripts.venue_agent_tool import normalize_venue_name


VENUES_ROOT = Path("/Volumes/VADER/Manifold/Neon_Blonde/Venues")
DEFAULT_LOCAL_MODEL_URL = "http://127.0.0.1:8080/completion"


@dataclass(frozen=True)
class LocalGig:
    venue: str
    city: str
    date: str
    time: str


def safe_folder_name(value: str) -> str:
    cleaned = re.sub(r"[/:\"]+", "", value).replace("'", "")
    return re.sub(r"\s+", " ", cleaned).strip()


def gig_folder_name(venue: str, gig_date: str) -> str:
    return f"{safe_folder_name(venue)} - {gig_date}"


def resolve_venue_folder(venue: str, venues_root: Path) -> Path | None:
    target = normalize_venue_name(venue)
    for child in venues_root.iterdir() if venues_root.exists() else []:
        if child.is_dir() and normalize_venue_name(child.name) == target:
            return child
    return None


def build_receipt(gig: LocalGig, created_venue_folder: bool, created_gig_folder: bool) -> str:
    status = "needs_review" if created_venue_folder else "success"
    return "\n".join(
        [
            "# Local Gig Folder Receipt",
            "",
            f"- Status: {status}",
            f"- Venue: {gig.venue}",
            f"- City: {gig.city}",
            f"- Date: {gig.date}",
            f"- Time: {gig.time}",
            f"- Venue folder created: {str(created_venue_folder).lower()}",
            f"- Gig folder created: {str(created_gig_folder).lower()}",
            "- Calendar source: Neon Blonde public calendar",
            "",
            "## Protected Writes",
            "",
            "- Google Calendar updated: false",
            "- Band Sheet updated: false",
            "- Google Drive folder updated: false",
            "- Email sent: false",
            "",
        ]
    )


def build_local_model_prompt(gig: LocalGig) -> str:
    return (
        "Create a short read-only local digest for this Neon Blonde gig folder.\n\n"
        f"Venue: {gig.venue}\n"
        f"City: {gig.city}\n"
        f"Date: {gig.date}\n"
        f"Time: {gig.time}\n\n"
        "Include likely follow-up questions and missing details to check. "
        "Do not confirm the booking, edit the calendar, send email, update payment status, or publish anything."
    )


def request_local_model_digest(gig: LocalGig, model_url: str = DEFAULT_LOCAL_MODEL_URL) -> str:
    payload = json.dumps({"prompt": build_local_model_prompt(gig), "n_predict": 350}).encode("utf-8")
    request = urllib.request.Request(model_url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("content") or data.get("response") or "").strip()


def write_local_model_file(
    gig: LocalGig,
    gig_folder: Path,
    *,
    use_local_model: bool = False,
    model_url: str = DEFAULT_LOCAL_MODEL_URL,
) -> Path:
    path = gig_folder / "LOCAL_MODEL_DIGEST.md"
    if use_local_model:
        try:
            digest = request_local_model_digest(gig, model_url)
            if digest:
                path.write_text(digest + "\n", encoding="utf-8")
                return path
        except Exception as exc:
            path.write_text(
                "# Local Model Digest\n\n"
                f"Local model unavailable: {exc}\n\n"
                "Folder creation succeeded. Run this digest again when the local model is available.\n",
                encoding="utf-8",
            )
            return path

    path.write_text(
        "# Local Model Digest\n\n"
        "Pending local model run.\n\n"
        + build_local_model_prompt(gig)
        + "\n",
        encoding="utf-8",
    )
    return path


def sync_local_gig_folder(
    gig: LocalGig,
    venues_root: Path = VENUES_ROOT,
    *,
    write_model_file: bool = True,
    use_local_model: bool = False,
    model_url: str = DEFAULT_LOCAL_MODEL_URL,
) -> dict:
    venues_root.mkdir(parents=True, exist_ok=True)
    venue_folder = resolve_venue_folder(gig.venue, venues_root)
    created_venue_folder = False
    if venue_folder is None:
        venue_folder = venues_root / safe_folder_name(gig.venue)
        venue_folder.mkdir(parents=True, exist_ok=True)
        created_venue_folder = True

    gig_folder = venue_folder / gig_folder_name(venue_folder.name, gig.date)
    created_gig_folder = not gig_folder.exists()
    gig_folder.mkdir(parents=True, exist_ok=True)
    receipt_path = gig_folder / "LOCAL_GIG_RECEIPT.md"
    receipt_path.write_text(build_receipt(gig, created_venue_folder, created_gig_folder), encoding="utf-8")

    model_path = None
    if write_model_file:
        model_path = write_local_model_file(gig, gig_folder, use_local_model=use_local_model, model_url=model_url)

    return {
        "status": "needs_review" if created_venue_folder else "success",
        "venue": gig.venue,
        "date": gig.date,
        "venue_folder": str(venue_folder),
        "gig_folder": str(gig_folder),
        "receipt_path": str(receipt_path),
        "local_model_path": str(model_path) if model_path else None,
        "created_venue_folder": created_venue_folder,
        "created_gig_folder": created_gig_folder,
    }


def fetch_calendar_gigs(calendar_url: str = PUBLIC_CALENDAR_ICS_URL) -> list[LocalGig]:
    with urllib.request.urlopen(calendar_url, timeout=20) as response:
        ics = response.read().decode("utf-8")
    return [LocalGig(venue=gig["venue"], city=gig["city"], date=gig["date"], time=gig["time"]) for gig in parse_calendar_ics(ics)]


def _local_gig_from_start(title: str, location: str, start: str) -> LocalGig:
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    hour = start_dt.hour % 12 or 12
    suffix = "am" if start_dt.hour < 12 else "pm"
    minute = f":{start_dt.minute:02d}" if start_dt.minute else ""
    return LocalGig(venue=title.strip(), city=location.strip(), date=start_dt.date().isoformat(), time=f"{hour}{minute}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create local per-venue gig folders from Neon Blonde calendar data.")
    parser.add_argument("--title", help="Single event title / venue name.")
    parser.add_argument("--location", help="Single event city.")
    parser.add_argument("--start", help="Single event start datetime, ISO format.")
    parser.add_argument("--sync-calendar", action="store_true", help="Sync all future public-calendar gigs.")
    parser.add_argument("--calendar-url", default=PUBLIC_CALENDAR_ICS_URL)
    parser.add_argument("--venues-root", default=str(VENUES_ROOT))
    parser.add_argument("--use-local-model", action="store_true")
    parser.add_argument("--local-model-url", default=DEFAULT_LOCAL_MODEL_URL)
    args = parser.parse_args()

    if args.sync_calendar:
        gigs = fetch_calendar_gigs(args.calendar_url)
    elif args.title and args.location and args.start:
        gigs = [_local_gig_from_start(args.title, args.location, args.start)]
    else:
        parser.error("Use --sync-calendar or provide --title, --location, and --start")

    results = [
        sync_local_gig_folder(
            gig,
            Path(args.venues_root),
            use_local_model=args.use_local_model,
            model_url=args.local_model_url,
        )
        for gig in gigs
    ]
    print(json.dumps({"status": "success", "count": len(results), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
