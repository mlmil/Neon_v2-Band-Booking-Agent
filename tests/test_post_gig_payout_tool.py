import csv
import tempfile
import unittest
from pathlib import Path

from scripts.post_gig_payout_tool import build_payout_row, upsert_payout_row


class PostGigPayoutToolTests(unittest.TestCase):
    def test_builds_payout_row(self):
        row = build_payout_row(
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_received="400",
            tip_jar_received="125",
            venmo_received="50",
        )

        self.assertEqual(row["VENUE"], "Tony's Pizza")
        self.assertEqual(row["CITY"], "Ventura")
        self.assertEqual(row["DATE"], "2026-06-12")
        self.assertEqual(row["PAYOUT"], "$400.00")
        self.assertEqual(row["TIP_JAR"], "$125.00")
        self.assertEqual(row["VENMO"], "$50.00")

    def test_empty_financials(self):
        row = build_payout_row(
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_received="0",
            tip_jar_received="",
            venmo_received="",
        )

        self.assertEqual(row["PAYOUT"], "")
        self.assertEqual(row["TIP_JAR"], "")
        self.assertEqual(row["VENMO"], "")

    def test_upsert_replaces_existing_gig_without_duplicating_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "payouts.csv"
            first = build_payout_row(
                venue="Tony's Pizza",
                city="Ventura",
                date="2026-06-12",
                base_pay_received="400",
                tip_jar_received="0",
                venmo_received="0",
            )
            updated = build_payout_row(
                venue="Tony's Pizza",
                city="Ventura",
                date="2026-06-12",
                base_pay_received="500",
                tip_jar_received="100",
                venmo_received="25",
            )

            upsert_payout_row(ledger, first)
            receipt = upsert_payout_row(ledger, updated)

            with ledger.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(receipt["action"], "updated")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["VENUE"], "TOTAL")
        self.assertEqual(rows[1]["PAYOUT"], "$500.00")
        self.assertEqual(rows[1]["TIP_JAR"], "$100.00")
        self.assertEqual(rows[1]["VENMO"], "$25.00")

    def test_migrates_legacy_tips_column(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "payouts.csv"
            ledger.write_text(
                "VENUE,CITY,DATE,PAYOUT,TIPS\n"
                "TOTAL,ALL TIME,,$400.00,$75.00\n"
                "Tony's Pizza,Ventura,2026-06-12,$400.00,$75.00\n",
                encoding="utf-8",
            )
            updated = build_payout_row(
                venue="Leashless",
                city="Ventura",
                date="2026-06-13",
                base_pay_received="500",
                tip_jar_received="100",
                venmo_received="50",
            )

            upsert_payout_row(ledger, updated)
            with ledger.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(rows[1]["TIP_JAR"], "$75.00")
        self.assertEqual(rows[1]["VENMO"], "")
        self.assertEqual(rows[0]["TIP_JAR"], "$175.00")
        self.assertEqual(rows[0]["VENMO"], "$50.00")


if __name__ == "__main__":
    unittest.main()
