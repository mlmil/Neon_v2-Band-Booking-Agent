import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.post_gig_reminder import due_for_email, missing_closeouts, read_ledger_rows, run_reminders


PACIFIC = ZoneInfo("America/Los_Angeles")


class PostGigReminderTests(unittest.TestCase):
    def test_finds_missing_split_payout_fields_after_delay(self):
        queue_rows = [
            {
                "gig_id": "tonys-2026-06-18",
                "venue": "Tony's Pizza",
                "city": "Ventura",
                "date": "2026-06-18",
                "end_at": "2026-06-18T22:00:00-07:00",
                "queue_status": "needs_closeout",
            }
        ]
        ledger_rows = {
            ("2026-06-18", "tonys pizza"): {
                "VENUE": "Tony's Pizza",
                "DATE": "2026-06-18",
                "PAYOUT": "$500.00",
                "TIP_JAR": "",
                "VENMO": "",
            }
        }

        missing = missing_closeouts(
            queue_rows,
            ledger_rows,
            now=datetime(2026, 6, 19, 2, 0, tzinfo=PACIFIC),
            delay_hours=3,
        )

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].missing_fields, ["TIP_JAR", "VENMO"])

    def test_old_gigs_do_not_require_venmo(self):
        missing = missing_closeouts(
            [
                {
                    "gig_id": "tonys-2026-06-12",
                    "venue": "Tony's Pizza",
                    "city": "Ventura",
                    "date": "2026-06-12",
                    "end_at": "2026-06-12T22:00:00-07:00",
                    "queue_status": "needs_closeout",
                }
            ],
            {
                ("2026-06-12", "tonys pizza"): {
                    "VENUE": "Tony's Pizza",
                    "DATE": "2026-06-12",
                    "PAYOUT": "$500.00",
                    "TIP_JAR": "$125.00",
                    "VENMO": "",
                }
            },
            now=datetime(2026, 6, 13, 2, 0, tzinfo=PACIFIC),
            delay_hours=3,
        )

        self.assertEqual(missing, [])

    def test_daily_throttle(self):
        item = missing_closeouts(
            [
                {
                    "gig_id": "tonys",
                    "venue": "Tony's Pizza",
                    "city": "Ventura",
                    "date": "2026-06-12",
                    "end_at": "2026-06-12T22:00:00-07:00",
                    "queue_status": "needs_closeout",
                }
            ],
            {},
            now=datetime(2026, 6, 13, 2, 0, tzinfo=PACIFIC),
        )[0]

        self.assertEqual(due_for_email([item], {}, now=datetime(2026, 6, 13, 9, 0, tzinfo=PACIFIC)), [item])
        self.assertEqual(due_for_email([item], {"tonys": "2026-06-13"}, now=datetime(2026, 6, 13, 9, 0, tzinfo=PACIFIC)), [])

    def test_dry_run_does_not_write_state_or_send(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue = root / "queue.csv"
            ledger = root / "ledger.csv"
            state = root / "state.json"
            with queue.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["gig_id", "venue", "city", "date", "start_at", "end_at", "queue_status"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "gig_id": "tonys",
                        "venue": "Tony's Pizza",
                        "city": "Ventura",
                        "date": "2026-06-12",
                        "start_at": "2026-06-12T19:00:00-07:00",
                        "end_at": "2026-06-12T22:00:00-07:00",
                        "queue_status": "needs_closeout",
                    }
                )
            ledger.write_text("VENUE,CITY,DATE,PAYOUT,TIP_JAR,VENMO\n", encoding="utf-8")

            receipt = run_reminders(
                queue_path=queue,
                ledger_path=ledger,
                state_path=state,
                refresh=False,
                dry_run=True,
                now=datetime(2026, 6, 13, 9, 0, tzinfo=PACIFIC),
            )

        self.assertEqual(receipt["sent"], 1)
        self.assertEqual(receipt["receipt"]["status"], "dry_run")
        self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
