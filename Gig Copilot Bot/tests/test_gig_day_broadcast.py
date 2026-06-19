import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from gig_copilot_bot.gig_day_broadcast import (
    GigDayBroadcaster,
    build_gig_day_message,
    find_gigs_for_date,
)


class GigDayBroadcastTests(unittest.TestCase):
    def test_finds_calendar_gigs_for_target_date(self) -> None:
        gigs = [
            {"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"},
            {"date": "2026-07-19", "venue": "Cruisery", "city": "Ventura", "time": "8pm"},
        ]

        matches = find_gigs_for_date(gigs, date(2026, 7, 18))

        self.assertEqual(matches, [gigs[0]])

    def test_builds_plain_band_group_message(self) -> None:
        message = build_gig_day_message(
            {"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}
        )

        self.assertIn("Gig today: Santa Barbara Yacht Club", message)
        self.assertIn("Santa Barbara", message)
        self.assertIn("6pm", message)
        self.assertIn("Reply here", message)

    def test_broadcaster_sends_once_and_writes_receipt(self) -> None:
        sent: list[tuple[int, str]] = []

        with TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipts.json"
            broadcaster = GigDayBroadcaster(
                group_chat_id=-1004424634571,
                receipt_path=receipt_path,
                send_message=lambda chat_id, text: sent.append((chat_id, text)),
            )

            result = broadcaster.send_for_gigs(
                [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}],
                target_date=date(2026, 7, 18),
            )
            second = broadcaster.send_for_gigs(
                [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}],
                target_date=date(2026, 7, 18),
            )

            receipts = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(result["sent"], 1)
        self.assertEqual(second["sent"], 0)
        self.assertEqual(sent[0][0], -1004424634571)
        self.assertIn("Santa Barbara Yacht Club", sent[0][1])
        self.assertEqual(len(receipts["sent"]), 1)

    def test_dry_run_does_not_send_or_write_receipt(self) -> None:
        sent: list[tuple[int, str]] = []

        with TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "receipts.json"
            broadcaster = GigDayBroadcaster(
                group_chat_id=-1004424634571,
                receipt_path=receipt_path,
                send_message=lambda chat_id, text: sent.append((chat_id, text)),
            )

            result = broadcaster.send_for_gigs(
                [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}],
                target_date=date(2026, 7, 18),
                dry_run=True,
            )

        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["would_send"], 1)
        self.assertEqual(sent, [])
        self.assertFalse(receipt_path.exists())


if __name__ == "__main__":
    unittest.main()
