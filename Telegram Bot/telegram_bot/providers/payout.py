from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_gig_payout_tool import DEFAULT_LEDGER, build_payout_row, upsert_payout_row
from scripts.post_gig_queue_sync import DEFAULT_QUEUE


@dataclass(frozen=True)
class ParsedPayout:
    payout: str = "0"
    tip_jar: str = "0"
    venmo: str = "0"

    @property
    def has_any_amount(self) -> bool:
        return any(value != "0" for value in (self.payout, self.tip_jar, self.venmo))


class PayoutCaptureProvider:
    def __init__(self, *, queue_path: Path = DEFAULT_QUEUE, ledger_path: Path = DEFAULT_LEDGER):
        self.queue_path = queue_path
        self.ledger_path = ledger_path

    def maybe_record(self, message_text: str) -> str | None:
        parsed = parse_payout_message(message_text)
        if parsed is None:
            return None

        gig = self._oldest_open_closeout()
        if gig is None:
            return "I heard payout numbers, but there is no open post-gig closeout item. Send /closeout first."

        row = build_payout_row(
            venue=gig["venue"],
            city=gig.get("city", ""),
            date=gig["date"],
            base_pay_received=parsed.payout,
            tip_jar_received=parsed.tip_jar,
            venmo_received=parsed.venmo,
        )
        receipt = upsert_payout_row(self.ledger_path, row)
        return "\n".join(
            [
                f"Logged post-gig payout for {row['VENUE']} on {row['DATE']}.",
                f"Payout: {row['PAYOUT'] or '$0.00'}",
                f"Tip jar: {row['TIP_JAR'] or '$0.00'}",
                f"Venmo: {row['VENMO'] or '$0.00'}",
                f"Ledger action: {receipt['action']}.",
            ]
        )

    def _oldest_open_closeout(self) -> dict[str, str] | None:
        if not self.queue_path.exists():
            return None
        with self.queue_path.open(newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row.get("queue_status") == "needs_closeout"]
        if not rows:
            return None
        rows.sort(key=lambda row: (row.get("date", ""), row.get("venue", "")))
        return rows[0]


def parse_payout_message(message_text: str) -> ParsedPayout | None:
    text = message_text.lower().replace("$", "")
    if not any(keyword in text for keyword in ("tip", "jar", "venmo", "payout", "paid", "pay ")):
        return None

    payout = _extract_amount(text, ["payout", "base pay", "paid", "pay"])
    tip_jar = _extract_amount(text, ["tip jar", "jar", "cash tips", "tips", "tip"])
    venmo = _extract_amount(text, ["venmo"])
    parsed = ParsedPayout(payout=payout, tip_jar=tip_jar, venmo=venmo)
    return parsed if parsed.has_any_amount else None


def _extract_amount(text: str, labels: list[str]) -> str:
    for label in labels:
        escaped = re.escape(label)
        patterns = [
            rf"{escaped}\s*(?:was|is|were|of|for|:)?\s*(\d+(?:\.\d{{1,2}})?)",
            rf"(\d+(?:\.\d{{1,2}})?)\s*(?:in|on|from|for)?\s*(?:the\s+)?{escaped}",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        if "hundred" in text and re.search(rf"{escaped}.*hundred|hundred.*{escaped}", text):
            return "100"
    return "0"
