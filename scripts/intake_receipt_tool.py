#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.intake_email_parser import parse_booking_request


DEFAULT_RECEIPT_DIR = Path("data/intake/receipts")


def slugify(value: str | None, fallback: str = "intake") -> str:
    value = value or fallback
    lowered = value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered)
    return cleaned.strip("-") or fallback


def receipt_filename(venue: str | None, requested_date: str | None, subject: str | None) -> str:
    date_part = requested_date or datetime.now(timezone.utc).date().isoformat()
    venue_part = slugify(venue, "unknown-venue")
    subject_part = slugify(subject, "booking-request")
    return f"{date_part}-{venue_part}-{subject_part}.json"


def build_intake_receipt(
    email_text: str,
    sender: str,
    subject: str,
    source_date: str,
    message_id: str | None = None,
) -> dict:
    parsed = parse_booking_request(email_text)
    next_step = (
        "Mike reviews the request and decides whether to add it to the calendar."
        if parsed["status"] == "ready_for_mike_review"
        else "Ask for the missing booking details before calendar review."
    )
    return {
        "phase": "Intake Phase",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": parsed["status"],
        "source": {
            "sender": sender,
            "subject": subject,
            "date": source_date,
            "message_id": message_id,
        },
        "request": {
            "venue": parsed["venue"],
            "date": parsed["date"],
            "time": parsed["time"],
            "city": parsed["city"],
            "missing_fields": parsed["missing_fields"],
            "review_flags": parsed["review_flags"],
        },
        "next_step": next_step,
        "acknowledgment_draft": parsed["acknowledgment_draft"],
        "protected_writes": {
            "calendar_updated": False,
            "bandsheet_updated": False,
            "email_sent": False,
        },
    }


def write_intake_receipt(receipt: dict, receipt_dir: Path = DEFAULT_RECEIPT_DIR) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    filename = receipt_filename(
        receipt["request"].get("venue"),
        receipt["request"].get("date"),
        receipt["source"].get("subject"),
    )
    path = receipt_dir / filename
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a local Neon V2 Intake Phase receipt from email text.")
    parser.add_argument("--text", help="Raw email text to parse.")
    parser.add_argument("--file", help="Path to a text file containing the raw email.")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--source-date", required=True)
    parser.add_argument("--message-id")
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    args = parser.parse_args()

    if args.file:
        email_text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        email_text = args.text
    else:
        parser.error("Provide --text or --file")

    receipt = build_intake_receipt(
        email_text=email_text,
        sender=args.sender,
        subject=args.subject,
        source_date=args.source_date,
        message_id=args.message_id,
    )
    path = write_intake_receipt(receipt, Path(args.receipt_dir))
    print(json.dumps({"status": "receipt_written", "path": str(path), "receipt": receipt}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
