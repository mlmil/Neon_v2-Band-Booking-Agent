from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


DEFAULT_LEDGER = Path("/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv")
FIELDNAMES = [
    "VENUE",
    "CITY",
    "DATE",
    "PAYOUT",
    "TIP_JAR",
    "VENMO",
]


def _money(value: str | int | float | Decimal, field_name: str) -> Decimal:
    try:
        clean_val = str(value or "0").replace("$", "").replace(",", "")
        amount = Decimal(clean_val).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a valid amount") from exc
    if amount < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return amount


def _format_money(value: Decimal) -> str:
    return f"${value:.2f}"


def normalize_money(value: object) -> str:
    if value is None:
        return ""
    clean_val = str(value).strip()
    if not clean_val:
        return ""
    amount = _money(clean_val, "money")
    return _format_money(amount) if amount > 0 else ""


def normalize_ledger_row(row: dict[str, str]) -> dict[str, str]:
    tip_jar = row.get("TIP_JAR", "") or row.get("TIPS", "")
    return {
        "VENUE": row.get("VENUE", "").strip(),
        "CITY": row.get("CITY", "").strip(),
        "DATE": row.get("DATE", "").strip(),
        "PAYOUT": normalize_money(row.get("PAYOUT", "")),
        "TIP_JAR": normalize_money(tip_jar),
        "VENMO": normalize_money(row.get("VENMO", "")),
    }

def normalize_venue(value: str) -> str:
    v = value.lower().strip()
    v = v.replace("'", "").replace("&", "and")
    v = re.sub(r"[^\w\s]", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    aliases = {
        "the cruisery": "cruisery",
        "parque 1055": "parquee 1055",
        "sewer": "the sewer",
        "tonys pizza": "tonys pizza",
        "m special": "ms special",
        "harrys night club and beach bar": "harrys",
        "harrys nightclub": "harrys",
        "fox wine co topa topa": "fox wine",
        "fox wine company": "fox wine",
        "fig mountain sb": "fig mountain",
        "fig mt los olivos": "fig mountain",
        "santa barbara yacht club": "yacht club",
        "fess parkers": "fess parker",
    }
    return aliases.get(v, v)

def row_key(date_str: str, venue_str: str) -> tuple[str, str]:
    return (date_str.strip(), normalize_venue(venue_str))


def build_payout_row(
    *,
    gig_id: str = "",
    venue: str,
    city: str,
    date: str,
    base_pay_expected: str | int | float | Decimal = 0,
    base_pay_received: str | int | float | Decimal = 0,
    tip_jar_received: str | int | float | Decimal = 0,
    venmo_received: str | int | float | Decimal = 0,
    tips_received: str | int | float | Decimal | None = None,
    payment_method: str = "",
    received_by: str = "",
    payment_status: str | None = None,
    payment_handle: str = "",
    entered_by: str = "Mike",
    notes: str = "",
    now: datetime | None = None,
) -> dict[str, str]:
    """Build one authoritative payout ledger row."""
    required = {
        "venue": venue,
        "date": date,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    received = _money(base_pay_received, "base_pay_received")
    legacy_tips = tip_jar_received if tips_received is None else tips_received
    tip_jar = _money(legacy_tips, "tip_jar_received")
    venmo = _money(venmo_received, "venmo_received")

    return {
        "VENUE": venue.strip(),
        "CITY": city.strip(),
        "DATE": date.strip(),
        "PAYOUT": _format_money(received) if received > 0 else "",
        "TIP_JAR": _format_money(tip_jar) if tip_jar > 0 else "",
        "VENMO": _format_money(venmo) if venmo > 0 else "",
    }


def upsert_payout_row(path: str | Path, row: dict[str, str]) -> dict[str, str]:
    """Insert or replace a payout row by date and venue and return a local receipt."""
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = []
    action = "created"

    if ledger_path.exists():
        with ledger_path.open(newline="", encoding="utf-8") as handle:
            existing_rows = [normalize_ledger_row(existing) for existing in csv.DictReader(handle)]

    output_rows = []
    clean_row = normalize_ledger_row(row)
    target_key = row_key(clean_row["DATE"], clean_row["VENUE"])

    for existing in existing_rows:
        if existing.get("VENUE", "") == "TOTAL":
            continue
        ex_key = row_key(existing.get("DATE", ""), existing.get("VENUE", ""))
        if ex_key == target_key:
            replacement = dict(existing)
            replacement["PAYOUT"] = clean_row["PAYOUT"]
            replacement["TIP_JAR"] = clean_row["TIP_JAR"]
            replacement["VENMO"] = clean_row["VENMO"]
            if clean_row["CITY"]:
                replacement["CITY"] = clean_row["CITY"]
            output_rows.append(replacement)
            action = "updated"
        else:
            output_rows.append(existing)

    if action == "created":
        output_rows.append(clean_row)

    output_rows.sort(key=lambda r: (r.get("DATE", ""), r.get("VENUE", "")))

    total_payout = 0.0
    total_tip_jar = 0.0
    total_venmo = 0.0
    for r in output_rows:
        try:
            total_payout += float(r.get("PAYOUT", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass
        try:
            total_tip_jar += float(r.get("TIP_JAR", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass
        try:
            total_venmo += float(r.get("VENMO", "").replace("$", "").replace(",", ""))
        except ValueError:
            pass

    total_row = {
        "VENUE": "TOTAL",
        "CITY": "ALL TIME",
        "DATE": "",
        "PAYOUT": f"${total_payout:.2f}" if total_payout > 0 else "",
        "TIP_JAR": f"${total_tip_jar:.2f}" if total_tip_jar > 0 else "",
        "VENMO": f"${total_venmo:.2f}" if total_venmo > 0 else "",
    }
    output_rows.insert(0, total_row)

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
        "venue": clean_row["VENUE"],
        "date": clean_row["DATE"],
        "ledger": str(ledger_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a supervised Post-Gig payout row.")
    parser.add_argument("--gig-id", default="")
    parser.add_argument("--venue", required=True)
    parser.add_argument("--city", default="")
    parser.add_argument("--date", required=True)
    parser.add_argument("--base-pay-expected", default=0)
    parser.add_argument("--base-pay-received", required=True)
    parser.add_argument("--tip-jar-received", default=0)
    parser.add_argument("--venmo-received", default=0)
    parser.add_argument("--tips-received", default=None, help="Legacy alias for --tip-jar-received.")
    parser.add_argument("--payment-method", default="")
    parser.add_argument("--payment-handle", default="")
    parser.add_argument("--received-by", default="")
    parser.add_argument("--payment-status", default="")
    parser.add_argument("--entered-by", default="Mike")
    parser.add_argument("--notes", default="")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args()

    try:
        row = build_payout_row(
            venue=args.venue,
            city=args.city,
            date=args.date,
            base_pay_received=args.base_pay_received,
            tip_jar_received=args.tip_jar_received,
            venmo_received=args.venmo_received,
            tips_received=args.tips_received,
        )
        receipt = upsert_payout_row(args.ledger, row)
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2))
        return 2

    print(json.dumps({"receipt": receipt, "row": row}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
