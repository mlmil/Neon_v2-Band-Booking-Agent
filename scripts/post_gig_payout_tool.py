from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_LEDGER = Path("data/post_gig/payouts.csv")
PRIMARY_VENMO_HANDLE = "@neonblondeband"
FIELDNAMES = [
    "gig_id",
    "venue",
    "city",
    "date",
    "base_pay_expected",
    "base_pay_received",
    "tips_received",
    "total_received",
    "payment_method",
    "payment_handle",
    "received_by",
    "still_owed",
    "payment_status",
    "entered_by",
    "entered_at",
    "updated_at",
    "notes",
]
VALID_STATUSES = {
    "payment_pending",
    "partial_payment",
    "needs_review",
    "paid_complete",
}


def _money(value: str | int | float | Decimal, field_name: str) -> Decimal:
    try:
        amount = Decimal(str(value or "0")).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a valid amount") from exc
    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return amount


def _format_money(value: Decimal) -> str:
    return f"{value:.2f}"


def build_payout_row(
    *,
    gig_id: str,
    venue: str,
    city: str,
    date: str,
    base_pay_expected: str | int | float | Decimal,
    base_pay_received: str | int | float | Decimal,
    tips_received: str | int | float | Decimal,
    payment_method: str,
    received_by: str,
    payment_status: str | None = None,
    payment_handle: str = "",
    entered_by: str = "Mike",
    notes: str = "",
    now: datetime | None = None,
) -> dict[str, str]:
    """Build one supervised Post-Gig ledger row."""
    required = {
        "gig_id": gig_id,
        "venue": venue,
        "date": date,
        "payment_method": payment_method,
        "received_by": received_by,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    expected = _money(base_pay_expected, "base_pay_expected")
    received = _money(base_pay_received, "base_pay_received")
    tips = _money(tips_received, "tips_received")
    total = received + tips
    still_owed = max(expected - received, Decimal("0.00"))

    requested_status = (payment_status or "").strip().lower()
    if requested_status and requested_status not in VALID_STATUSES:
        raise ValueError(f"unsupported payment_status: {requested_status}")
    if requested_status == "paid_complete" and still_owed > 0:
        raise ValueError("payment cannot be paid_complete while base pay is still owed")

    if requested_status:
        status = requested_status
    elif received == 0 and expected > 0:
        status = "payment_pending"
    elif still_owed > 0:
        status = "partial_payment"
    else:
        status = "needs_review"

    normalized_method = payment_method.strip()
    handle = payment_handle.strip()
    if normalized_method.lower() == "venmo" and not handle:
        handle = PRIMARY_VENMO_HANDLE

    timestamp = (now or datetime.now(timezone.utc)).isoformat()
    return {
        "gig_id": gig_id.strip(),
        "venue": venue.strip(),
        "city": city.strip(),
        "date": date.strip(),
        "base_pay_expected": _format_money(expected),
        "base_pay_received": _format_money(received),
        "tips_received": _format_money(tips),
        "total_received": _format_money(total),
        "payment_method": normalized_method,
        "payment_handle": handle,
        "received_by": received_by.strip(),
        "still_owed": _format_money(still_owed),
        "payment_status": status,
        "entered_by": entered_by.strip() or "Mike",
        "entered_at": timestamp,
        "updated_at": timestamp,
        "notes": notes.strip(),
    }


def upsert_payout_row(path: str | Path, row: dict[str, str]) -> dict[str, str]:
    """Insert or replace a payout row by gig_id and return a local receipt."""
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = []
    action = "created"

    if ledger_path.exists():
        with ledger_path.open(newline="", encoding="utf-8") as handle:
            existing_rows = list(csv.DictReader(handle))

    output_rows = []
    for existing in existing_rows:
        if existing.get("gig_id") == row["gig_id"]:
            replacement = dict(row)
            replacement["entered_at"] = existing.get("entered_at") or row["entered_at"]
            output_rows.append(replacement)
            action = "updated"
        else:
            output_rows.append(existing)

    if action == "created":
        output_rows.append(row)

    with tempfile.NamedTemporaryFile(
        "w",
        newline="",
        encoding="utf-8",
        dir=ledger_path.parent,
        delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
        temp_name = handle.name

    os.replace(temp_name, ledger_path)
    return {
        "status": "success",
        "action": action,
        "gig_id": row["gig_id"],
        "payment_status": row["payment_status"],
        "ledger": str(ledger_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a supervised Post-Gig payout row.")
    parser.add_argument("--gig-id", required=True)
    parser.add_argument("--venue", required=True)
    parser.add_argument("--city", default="")
    parser.add_argument("--date", required=True)
    parser.add_argument("--base-pay-expected", required=True)
    parser.add_argument("--base-pay-received", required=True)
    parser.add_argument("--tips-received", required=True)
    parser.add_argument("--payment-method", required=True)
    parser.add_argument("--payment-handle", default="")
    parser.add_argument("--received-by", required=True)
    parser.add_argument("--payment-status", choices=sorted(VALID_STATUSES))
    parser.add_argument("--entered-by", default="Mike")
    parser.add_argument("--notes", default="")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args()

    try:
        row = build_payout_row(
            gig_id=args.gig_id,
            venue=args.venue,
            city=args.city,
            date=args.date,
            base_pay_expected=args.base_pay_expected,
            base_pay_received=args.base_pay_received,
            tips_received=args.tips_received,
            payment_method=args.payment_method,
            payment_handle=args.payment_handle,
            received_by=args.received_by,
            payment_status=args.payment_status,
            entered_by=args.entered_by,
            notes=args.notes,
        )
        receipt = upsert_payout_row(args.ledger, row)
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2))
        return 2

    print(json.dumps({"receipt": receipt, "row": row}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
