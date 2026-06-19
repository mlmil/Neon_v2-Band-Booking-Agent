import unittest
from pathlib import Path
from datetime import datetime

from scripts.post_gig_queue_sync import QueueGig
import scripts.payout_csv_sync as sync

class TestPayoutCsvSync(unittest.TestCase):
    def test_model_fields(self):
        self.assertEqual(sync.FIELDNAMES, ["VENUE", "CITY", "DATE", "PAYOUT", "TIP_JAR", "VENMO"])

    def test_normalize_money(self):
        self.assertEqual(sync.normalize_money("$500.00"), "$500.00")
        self.assertEqual(sync.normalize_money("500"), "$500.00")
        self.assertEqual(sync.normalize_money(""), "")
        self.assertEqual(sync.normalize_money(None), "")
        self.assertEqual(sync.normalize_money("missing value"), "")
        self.assertEqual(sync.normalize_money("500.5"), "$500.50")

    def test_normalize_venue(self):
        self.assertEqual(sync.normalize_venue("The Sewer "), "the sewer")
        self.assertEqual(sync.normalize_venue("Tony's Pizza"), "tonys pizza")
        self.assertEqual(sync.normalize_venue("Gig at M Special"), "ms special")

    def test_row_key(self):
        self.assertEqual(
            sync.row_key({"VENUE": "The Sewer ", "DATE": "2026-03-06"}),
            ("2026-03-06", "the sewer")
        )

    def test_normalize_row(self):
        raw = {
            "Venue": "The Sewer",
            "City": "Ventura",
            "Date": "3/6/2026",
            "Payout": "$400.00",
            "Tips": "$42.00",
            "Venmo": "$12.00",
        }
        expected = {
            "VENUE": "The Sewer",
            "CITY": "Ventura",
            "DATE": "2026-03-06",
            "PAYOUT": "$400.00",
            "TIP_JAR": "$42.00",
            "VENMO": "$12.00",
        }
        self.assertEqual(sync.normalize_row(raw), expected)

    def test_parse_numbers_rows(self):
        raw = [{
            "Venue": "The Sewer",
            "City": "Ventura",
            "Date": "3/6/2026",
            "Payout": "$400.00",
            "Tips": "$42.00",
        }]
        expected = [{
            "VENUE": "The Sewer",
            "CITY": "Ventura",
            "DATE": "2026-03-06",
            "PAYOUT": "$400.00",
            "TIP_JAR": "$42.00",
            "VENMO": "",
        }]
        self.assertEqual(sync.parse_numbers_rows(raw), expected)

    def test_merge_rows(self):
        existing = [{
            "VENUE": "The Sewer",
            "CITY": "Ventura",
            "DATE": "2026-03-06",
            "PAYOUT": "$400.00",
            "TIPS": "$42.00",
        }]
        gig = QueueGig(
            gig_id="sewer-2026-03-06",
            venue="The Sewer",
            city="Ventura",
            start_at="2026-03-06T19:00:00",
            end_at="2026-03-06T22:00:00"
        )
        new_gig = QueueGig(
            gig_id="tonys-2026-03-07",
            venue="Tony's Pizza",
            city="Ventura",
            start_at="2026-03-07T19:00:00",
            end_at="2026-03-07T22:00:00"
        )

        merged, counts = sync.merge_rows(existing, [gig, new_gig])
        sewer_row = next(row for row in merged if row["VENUE"] == "The Sewer")
        tonys_row = next(row for row in merged if row["VENUE"] == "Tony's Pizza")
        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0]["VENUE"], "TOTAL")
        self.assertEqual(sewer_row["PAYOUT"], "$400.00")
        self.assertEqual(sewer_row["TIP_JAR"], "$42.00")
        self.assertEqual(tonys_row["PAYOUT"], "")
        self.assertEqual(counts["matched"], 1)
        self.assertEqual(counts["created"], 1)
        self.assertEqual(counts["total"], 2)

if __name__ == "__main__":
    unittest.main()
