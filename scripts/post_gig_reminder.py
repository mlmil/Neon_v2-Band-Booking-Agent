#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_gig_payout_tool import DEFAULT_LEDGER, normalize_ledger_row, normalize_venue, row_key
from scripts.post_gig_queue_sync import DEFAULT_QUEUE, fetch_calendar_queue_gigs, sync_queue

PACIFIC = ZoneInfo("America/Los_Angeles")
DEFAULT_STATE = Path("data/post_gig/reminder_state.json")
DEFAULT_RECIPIENTS = ["neonblondevc@gmail.com", "sin.chonies.inc@gmail.com"]
REQUIRED_FIELDS = ["PAYOUT", "TIP_JAR", "VENMO"]
VENMO_REQUIRED_FROM = "2026-06-17"


@dataclass(frozen=True)
class MissingCloseout:
    gig_id: str
    venue: str
    city: str
    date: str
    end_at: datetime
    missing_fields: list[str]


def read_queue_rows(queue_path: Path = DEFAULT_QUEUE) -> list[dict[str, str]]:
    if not queue_path.exists():
        return []
    with queue_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_ledger_rows(ledger_path: Path = DEFAULT_LEDGER) -> dict[tuple[str, str], dict[str, str]]:
    if not ledger_path.exists():
        return {}
    with ledger_path.open(newline="", encoding="utf-8") as handle:
        rows = [normalize_ledger_row(row) for row in csv.DictReader(handle)]
    return {
        row_key(row.get("DATE", ""), row.get("VENUE", "")): row
        for row in rows
        if row.get("VENUE") and row.get("VENUE") != "TOTAL"
    }


def missing_closeouts(
    queue_rows: list[dict[str, str]],
    ledger_rows: dict[tuple[str, str], dict[str, str]],
    *,
    now: datetime | None = None,
    delay_hours: int = 3,
    lookback_days: int | None = 30,
) -> list[MissingCloseout]:
    current_time = now or datetime.now(PACIFIC)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=PACIFIC)
    due_after = timedelta(hours=max(delay_hours, 0))
    cutoff = current_time - timedelta(days=max(lookback_days, 0)) if lookback_days is not None else None
    items: list[MissingCloseout] = []

    for row in queue_rows:
        if row.get("queue_status") != "needs_closeout":
            continue
        try:
            end_at = datetime.fromisoformat(row.get("end_at", ""))
        except ValueError:
            continue
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=PACIFIC)
        if cutoff is not None and end_at < cutoff:
            continue
        if current_time < end_at + due_after:
            continue

        key = row_key(row.get("date", ""), row.get("venue", ""))
        ledger = ledger_rows.get(key, {})
        required_fields = REQUIRED_FIELDS if row.get("date", "") >= VENMO_REQUIRED_FROM else ["PAYOUT", "TIP_JAR"]
        missing = [field for field in required_fields if not str(ledger.get(field, "")).strip()]
        if missing:
            items.append(
                MissingCloseout(
                    gig_id=row.get("gig_id", ""),
                    venue=row.get("venue", ""),
                    city=row.get("city", ""),
                    date=row.get("date", ""),
                    end_at=end_at,
                    missing_fields=missing,
                )
            )

    return sorted(items, key=lambda item: (item.date, normalize_venue(item.venue)))


def read_state(state_path: Path = DEFAULT_STATE) -> dict[str, str]:
    if not state_path.exists():
        return {}
    try:
        with state_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def write_state(state_path: Path, state: dict[str, str]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=state_path.parent, delete=False) as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, state_path)


def due_for_email(items: list[MissingCloseout], state: dict[str, str], *, now: datetime | None = None) -> list[MissingCloseout]:
    current_time = now or datetime.now(PACIFIC)
    today = current_time.astimezone(PACIFIC).date().isoformat()
    due = []
    for item in items:
        if state.get(item.gig_id) != today:
            due.append(item)
    return due


def build_email(items: list[MissingCloseout]) -> tuple[str, str]:
    subject = f"Neon post-gig payout needed: {len(items)} open show{'s' if len(items) != 1 else ''}"
    lines = [
        "Hey, these past gigs still need payout/tip info in the Neon payout spreadsheet:",
        "",
    ]
    for item in items:
        missing = ", ".join(item.missing_fields)
        city = f" ({item.city})" if item.city else ""
        lines.append(f"- {item.date}: {item.venue}{city} - missing {missing}")
    lines.extend(
        [
            "",
            "Update the spreadsheet, or text the Neon Telegram bot like:",
            "tip jar 200, Venmo 100, payout 500",
            "",
            "- Neon V2",
        ]
    )
    return subject, "\n".join(lines)


def send_agentmail(subject: str, body: str, recipients: list[str]) -> dict[str, object]:
    from scripts.agentmail_health_check import DEFAULT_INBOX
    from scripts.agentmail_send import send_agentmail as send

    return send(inbox=DEFAULT_INBOX, to=recipients, cc=[], subject=subject, text=body)


def refresh_queue(queue_path: Path, *, now: datetime | None = None, lookback_days: int = 30) -> dict[str, object]:
    current_time = now or datetime.now(PACIFIC)
    cutoff = current_time - timedelta(days=max(lookback_days, 0))
    gigs = fetch_calendar_queue_gigs()
    relevant = [gig for gig in gigs if datetime.fromisoformat(gig.end_at) >= cutoff]
    return sync_queue(relevant, queue_path, now=current_time)


def run_reminders(
    *,
    queue_path: Path = DEFAULT_QUEUE,
    ledger_path: Path = DEFAULT_LEDGER,
    state_path: Path = DEFAULT_STATE,
    recipients: list[str] | None = None,
    delay_hours: int = 3,
    lookback_days: int = 30,
    refresh: bool = True,
    dry_run: bool = False,
    now: datetime | None = None,
) -> dict[str, object]:
    if refresh:
        refresh_queue(queue_path, now=now, lookback_days=lookback_days)
    queue_rows = read_queue_rows(queue_path)
    ledger_rows = read_ledger_rows(ledger_path)
    missing = missing_closeouts(queue_rows, ledger_rows, now=now, delay_hours=delay_hours, lookback_days=lookback_days)
    state = read_state(state_path)
    due = due_for_email(missing, state, now=now)
    if not due:
        return {"status": "success", "missing": len(missing), "sent": 0}

    subject, body = build_email(due)
    target_recipients = recipients or DEFAULT_RECIPIENTS
    if dry_run:
        send_receipt = {"status": "dry_run", "to": target_recipients, "subject": subject, "body": body}
    else:
        send_receipt = send_agentmail(subject, body, target_recipients)

    if not dry_run and send_receipt.get("status") == "sent":
        current_time = now or datetime.now(PACIFIC)
        today = current_time.astimezone(PACIFIC).date().isoformat()
        for item in due:
            state[item.gig_id] = today
        write_state(state_path, state)

    return {
        "status": "success",
        "missing": len(missing),
        "sent": len(due),
        "receipt": send_receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Send repeat-until-filled Neon post-gig payout reminders.")
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--recipient", action="append", dest="recipients")
    parser.add_argument("--delay-hours", type=int, default=3)
    parser.add_argument("--lookback-days", type=int, default=30)
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        receipt = run_reminders(
            queue_path=args.queue,
            ledger_path=args.ledger,
            state_path=args.state,
            recipients=args.recipients,
            delay_hours=args.delay_hours,
            lookback_days=args.lookback_days,
            refresh=not args.no_refresh,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
