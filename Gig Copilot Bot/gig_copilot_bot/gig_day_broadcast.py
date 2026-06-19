from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable


SendMessage = Callable[[int, str], None]


def find_gigs_for_date(gigs: list[dict[str, str]], target_date: date) -> list[dict[str, str]]:
    target = target_date.isoformat()
    return [gig for gig in gigs if gig.get("date") == target]


def build_gig_day_message(gig: dict[str, str]) -> str:
    venue = gig.get("venue") or "venue TBD"
    city = gig.get("city") or "city TBD"
    time = gig.get("time") or "time TBD"
    return "\n".join(
        [
            f"Gig today: {venue}",
            f"City: {city}",
            f"Start: {time}",
            "",
            "Please check your travel/load-in plan now.",
            "Reply here if anything changed or if you are at risk of being late.",
        ]
    )


@dataclass
class GigDayBroadcaster:
    group_chat_id: int
    receipt_path: Path
    send_message: SendMessage

    def send_for_gigs(
        self,
        gigs: list[dict[str, str]],
        *,
        target_date: date,
        dry_run: bool = False,
    ) -> dict[str, object]:
        todays_gigs = find_gigs_for_date(gigs, target_date)
        receipts = self._load_receipts()
        sent_count = 0
        would_send = 0
        messages: list[str] = []

        for gig in todays_gigs:
            receipt_id = _receipt_id(gig)
            if receipt_id in receipts:
                continue
            message = build_gig_day_message(gig)
            messages.append(message)
            if dry_run:
                would_send += 1
                continue
            self.send_message(self.group_chat_id, message)
            receipts[receipt_id] = {
                "sent_at": datetime.now().isoformat(),
                "chat_id": self.group_chat_id,
                "gig": gig,
            }
            sent_count += 1

        if sent_count:
            self._write_receipts(receipts)

        return {
            "status": "success",
            "target_date": target_date.isoformat(),
            "matched": len(todays_gigs),
            "sent": sent_count,
            "would_send": would_send,
            "messages": messages,
        }

    def _load_receipts(self) -> dict[str, object]:
        if not self.receipt_path.exists():
            return {}
        try:
            payload = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        sent = payload.get("sent") if isinstance(payload, dict) else None
        return sent if isinstance(sent, dict) else {}

    def _write_receipts(self, receipts: dict[str, object]) -> None:
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipt_path.write_text(json.dumps({"sent": receipts}, indent=2, sort_keys=True), encoding="utf-8")


def _receipt_id(gig: dict[str, str]) -> str:
    date_value = gig.get("date", "unknown-date")
    venue = re.sub(r"[^a-z0-9]+", "-", gig.get("venue", "unknown-venue").lower()).strip("-")
    return f"{date_value}:{venue}"
