import csv
import tempfile
import unittest
from pathlib import Path

from telegram_bot.providers.payout import PayoutCaptureProvider, parse_payout_message


class PayoutProviderTests(unittest.TestCase):
    def test_parses_split_tip_dictation(self):
        parsed = parse_payout_message("We made tip jar 200, Venmo 100, payout 500")

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.tip_jar, "200")
        self.assertEqual(parsed.venmo, "100")
        self.assertEqual(parsed.payout, "500")

    def test_records_to_oldest_open_closeout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue = root / "queue.csv"
            ledger = root / "ledger.csv"
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

            reply = PayoutCaptureProvider(queue_path=queue, ledger_path=ledger).maybe_record(
                "tip jar 200 venmo 100 payout 500"
            )
            with ledger.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertIn("Logged post-gig payout for Tony's Pizza", reply)
        self.assertEqual(rows[1]["PAYOUT"], "$500.00")
        self.assertEqual(rows[1]["TIP_JAR"], "$200.00")
        self.assertEqual(rows[1]["VENMO"], "$100.00")


if __name__ == "__main__":
    unittest.main()
