#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_COLUMNS = [
    "lead_id",
    "venue_name",
    "city",
    "county",
    "region_priority",
    "status",
    "lead_score",
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


def validate_scout_csv(path: Path) -> dict:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return {
                "status": "blocked",
                "code": "SCOUT_SOURCE_INCOMPLETE",
                "failure_reason": f"Missing columns: {', '.join(missing)}",
            }
        invalid_statuses = []
        for row in reader:
            status = row.get("status", "")
            if status and status not in ALLOWED_STATUSES:
                invalid_statuses.append(status)
        if invalid_statuses:
            return {
                "status": "needs_review",
                "code": "SCOUT_STATUS_INVALID",
                "failure_reason": f"Invalid statuses: {', '.join(sorted(set(invalid_statuses)))}",
            }
    return {"status": "success"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()
    print(json.dumps(validate_scout_csv(Path(args.csv_path)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
