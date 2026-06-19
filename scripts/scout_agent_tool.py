#!/usr/bin/env python3
"""Scout Agent lead CSV validator and scoring tool.

Usage:
  python3 scout_agent_tool.py <csv_path>              # validate CSV
  python3 scout_agent_tool.py --score <csv_path>      # validate + emit stale/score warnings
  python3 scout_agent_tool.py --calc-score            # print scoring rubric help
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "lead_id",
    "venue_name",
    "city",
    "county",
    "region_priority",
    "status",
    "lead_score",
    "gig_type",
    "source_type",
    "source_url",
    "similar_bands_seen",
    "booking_contact_name",
    "booking_contact_email",
    "booking_contact_phone",
    "lead_owner",
    "next_action",
    "follow_up_date",
    "last_checked",
    "notes",
]

REQUIRED_NONEMPTY = ["lead_id", "venue_name", "city", "county", "region_priority", "status"]

ALLOWED_STATUSES = {
    "discovered",
    "researching",
    "qualified",
    "ready_to_contact",
    "contacted",
    "follow_up",
    "warm",
    "not_a_fit",
    "booked",
    "converted_to_venue_agent",
}

ALLOWED_GIG_TYPES = {"club", "festival", "municipal", "private_club"}

ALLOWED_SOURCE_TYPES = {
    "venue_website",
    "venue_calendar",
    "venue_social",
    "local_event_listing",
    "band_social",
    "chamber_of_commerce",
    "parks_rec",
    "fraternal_org",
    "referral",
    "other",
}

ALLOWED_OWNERS = {"Mike Miller", "Alfred Morlaes", "Curtis Clyde", "unassigned"}

ALLOWED_REGION_PRIORITIES = {"1", "2", "3"}

STALE_DAYS = 60
DATE_FORMAT = "%Y-%m-%d"


# ---------------------------------------------------------------------------
# Scoring rubric
# ---------------------------------------------------------------------------

SCORING_RUBRIC = {
    "adds": {
        "books_live_bands":          25,
        "similar_bands_seen":        20,
        "target_region_fit":         15,
        "clear_booking_contact":     15,
        "music_style_fit":           10,
        "supports_six_piece":        10,
        "high_value_gig_type":       15,
        "warm_connection_notes":      5,
    },
    "subtracts": {
        "no_clear_contact":         -20,
        "wrong_music_programming":  -20,
        "too_far":                  -15,
        "one_off_no_recurring":     -15,
        "do_not_contact":           -50,
    },
    "bands": {
        "high_priority":  (80, 100),
        "qualified":      (60, 79),
        "research_more":  (40, 59),
        "weak":           (0, 39),
    },
}


def calculate_lead_score(
    books_live_bands: bool = False,
    similar_bands_seen: bool = False,
    target_region_fit: bool = False,
    clear_booking_contact: bool = False,
    music_style_fit: bool = False,
    supports_six_piece: bool = False,
    high_value_gig_type: bool = False,
    warm_connection_notes: bool = False,
    no_clear_contact: bool = False,
    wrong_music_programming: bool = False,
    too_far: bool = False,
    one_off_no_recurring: bool = False,
    do_not_contact: bool = False,
) -> int:
    """Calculate a Scout lead score (0-100) from known signals.

    Pass True for each signal that applies. Score is clamped to 0-100.

    Example:
        score = calculate_lead_score(
            books_live_bands=True,
            similar_bands_seen=True,
            target_region_fit=True,
            clear_booking_contact=True,
            music_style_fit=True,
            supports_six_piece=True,
        )
        # → 100 (clamped from 110)
    """
    r = SCORING_RUBRIC
    score = 0
    if books_live_bands:       score += r["adds"]["books_live_bands"]
    if similar_bands_seen:     score += r["adds"]["similar_bands_seen"]
    if target_region_fit:      score += r["adds"]["target_region_fit"]
    if clear_booking_contact:  score += r["adds"]["clear_booking_contact"]
    if music_style_fit:        score += r["adds"]["music_style_fit"]
    if supports_six_piece:     score += r["adds"]["supports_six_piece"]
    if high_value_gig_type:    score += r["adds"]["high_value_gig_type"]
    if warm_connection_notes:  score += r["adds"]["warm_connection_notes"]
    if no_clear_contact:       score += r["subtracts"]["no_clear_contact"]
    if wrong_music_programming: score += r["subtracts"]["wrong_music_programming"]
    if too_far:                score += r["subtracts"]["too_far"]
    if one_off_no_recurring:   score += r["subtracts"]["one_off_no_recurring"]
    if do_not_contact:         score += r["subtracts"]["do_not_contact"]
    return max(0, min(100, score))


def score_band(score: int) -> str:
    """Return human-readable priority band for a score."""
    if score >= 80:
        return "high_priority"
    if score >= 60:
        return "qualified"
    if score >= 40:
        return "research_more"
    return "weak"


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _parse_date(val: str) -> date | None:
    try:
        return datetime.strptime(val.strip(), DATE_FORMAT).date()
    except (ValueError, AttributeError):
        return None


def validate_scout_csv(path: Path, check_scores: bool = False) -> dict:
    """Validate the Scout lead CSV.

    Returns a result dict with:
      status: "success" | "blocked" | "needs_review"
      code: error code string if not success
      failure_reason: human-readable description
      warnings: list of non-blocking issues
      row_errors: list of per-row problems
    """
    warnings: list[str] = []
    row_errors: list[str] = []

    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        # --- Column presence check (blocking) ---
        missing_cols = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
        if missing_cols:
            return {
                "status": "blocked",
                "code": "SCOUT_SOURCE_INCOMPLETE",
                "failure_reason": f"Missing columns: {', '.join(missing_cols)}",
                "warnings": [],
                "row_errors": [],
            }

        today = date.today()

        for i, row in enumerate(reader, start=2):  # row 1 = header
            ref = f"Row {i} ({row.get('lead_id', '?')} / {row.get('venue_name', '?')})"

            # --- Required non-empty fields ---
            for field in REQUIRED_NONEMPTY:
                if not row.get(field, "").strip():
                    row_errors.append(f"{ref}: '{field}' is empty")

            # --- Status ---
            status = row.get("status", "").strip()
            if status and status not in ALLOWED_STATUSES:
                row_errors.append(f"{ref}: invalid status '{status}'")

            # --- Gig type ---
            gig_type = row.get("gig_type", "").strip()
            if gig_type and gig_type not in ALLOWED_GIG_TYPES:
                row_errors.append(f"{ref}: invalid gig_type '{gig_type}'")

            # --- Source type ---
            source_type = row.get("source_type", "").strip()
            if source_type and source_type not in ALLOWED_SOURCE_TYPES:
                row_errors.append(f"{ref}: invalid source_type '{source_type}'")

            # --- Lead owner ---
            owner = row.get("lead_owner", "").strip()
            if owner and owner not in ALLOWED_OWNERS:
                row_errors.append(f"{ref}: invalid lead_owner '{owner}'")

            # --- Region priority ---
            priority = row.get("region_priority", "").strip()
            if priority and priority not in ALLOWED_REGION_PRIORITIES:
                row_errors.append(f"{ref}: invalid region_priority '{priority}' (must be 1, 2, or 3)")

            # --- Lead score range ---
            score_raw = row.get("lead_score", "").strip()
            if score_raw:
                try:
                    score_val = int(score_raw)
                    if not (0 <= score_val <= 100):
                        row_errors.append(f"{ref}: lead_score {score_val} out of range (0-100)")
                except ValueError:
                    row_errors.append(f"{ref}: lead_score '{score_raw}' is not an integer")

            # --- Date fields ---
            for date_field in ("follow_up_date", "last_checked"):
                val = row.get(date_field, "").strip()
                if val and _parse_date(val) is None:
                    row_errors.append(f"{ref}: {date_field} '{val}' not in YYYY-MM-DD format")

            # --- Stale lead warning ---
            last_checked_val = row.get("last_checked", "").strip()
            if last_checked_val:
                last_checked_date = _parse_date(last_checked_val)
                if last_checked_date and (today - last_checked_date).days > STALE_DAYS:
                    days_old = (today - last_checked_date).days
                    warnings.append(
                        f"{ref}: last_checked is {days_old} days ago (>{STALE_DAYS} day threshold)"
                    )

    if row_errors:
        return {
            "status": "needs_review",
            "code": "SCOUT_ROW_ERRORS",
            "failure_reason": f"{len(row_errors)} row error(s) found",
            "warnings": warnings,
            "row_errors": row_errors,
        }

    return {
        "status": "success",
        "warnings": warnings,
        "row_errors": [],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Scout lead CSV and optionally show scoring help."
    )
    parser.add_argument("csv_path", nargs="?", help="Path to scout-leads.csv")
    parser.add_argument(
        "--score",
        action="store_true",
        help="Include stale-lead warnings in output (same as default; kept for clarity)",
    )
    parser.add_argument(
        "--calc-score",
        action="store_true",
        help="Print scoring rubric and exit",
    )
    args = parser.parse_args()

    if args.calc_score:
        print(json.dumps(SCORING_RUBRIC, indent=2))
        return 0

    if not args.csv_path:
        parser.print_help()
        return 1

    result = validate_scout_csv(Path(args.csv_path), check_scores=args.score)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
