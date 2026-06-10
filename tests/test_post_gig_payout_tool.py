import csv
import tempfile
import unittest
from pathlib import Path

from scripts.post_gig_payout_tool import build_payout_row, upsert_payout_row


class PostGigPayoutToolTests(unittest.TestCase):
    def test_builds_payment_totals_without_counting_tips_toward_base_pay(self):
        row = build_payout_row(
            gig_id="tonys-2026-06-12",
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_expected="500",
            base_pay_received="400",
            tips_received="125",
            payment_method="cash",
            received_by="Mike",
        )

        self.assertEqual(row["total_received"], "525.00")
        self.assertEqual(row["still_owed"], "100.00")
        self.assertEqual(row["payment_status"], "partial_payment")

    def test_venmo_uses_primary_band_handle(self):
        row = build_payout_row(
            gig_id="tonys-2026-06-12",
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_expected="500",
            base_pay_received="500",
            tips_received="100",
            payment_method="Venmo",
            received_by="Mike",
        )

        self.assertEqual(row["payment_handle"], "@neonblondeband")
        self.assertEqual(row["payment_status"], "needs_review")

    def test_paid_complete_requires_no_outstanding_base_pay(self):
        with self.assertRaisesRegex(ValueError, "still owed"):
            build_payout_row(
                gig_id="tonys-2026-06-12",
                venue="Tony's Pizza",
                city="Ventura",
                date="2026-06-12",
                base_pay_expected="500",
                base_pay_received="400",
                tips_received="100",
                payment_method="Venmo",
                received_by="Mike",
                payment_status="paid_complete",
            )

    def test_paid_complete_must_be_explicit(self):
        pending_review = build_payout_row(
            gig_id="tonys-2026-06-12",
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_expected="500",
            base_pay_received="500",
            tips_received="100",
            payment_method="Venmo",
            received_by="Mike",
        )
        completed = build_payout_row(
            gig_id="tonys-2026-06-12",
            venue="Tony's Pizza",
            city="Ventura",
            date="2026-06-12",
            base_pay_expected="500",
            base_pay_received="500",
            tips_received="100",
            payment_method="Venmo",
            received_by="Mike",
            payment_status="paid_complete",
        )

        self.assertEqual(pending_review["payment_status"], "needs_review")
        self.assertEqual(completed["payment_status"], "paid_complete")

    def test_upsert_replaces_existing_gig_without_duplicating_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "payouts.csv"
            first = build_payout_row(
                gig_id="tonys-2026-06-12",
                venue="Tony's Pizza",
                city="Ventura",
                date="2026-06-12",
                base_pay_expected="500",
                base_pay_received="400",
                tips_received="0",
                payment_method="check",
                received_by="Mike",
            )
            updated = build_payout_row(
                gig_id="tonys-2026-06-12",
                venue="Tony's Pizza",
                city="Ventura",
                date="2026-06-12",
                base_pay_expected="500",
                base_pay_received="500",
                tips_received="100",
                payment_method="Venmo",
                received_by="Mike",
                payment_status="paid_complete",
            )

            upsert_payout_row(ledger, first)
            receipt = upsert_payout_row(ledger, updated)

            with ledger.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(receipt["action"], "updated")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["base_pay_received"], "500.00")
        self.assertEqual(rows[0]["payment_status"], "paid_complete")


if __name__ == "__main__":
    unittest.main()
