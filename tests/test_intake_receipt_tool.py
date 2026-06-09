import tempfile
import unittest
from pathlib import Path

from scripts.intake_receipt_tool import build_intake_receipt, receipt_filename, write_intake_receipt


class IntakeReceiptToolTests(unittest.TestCase):
    def test_build_intake_receipt_adds_source_metadata_and_next_step(self):
        receipt = build_intake_receipt(
            email_text="Can we book M Special on August 15 at 7pm in Goleta?",
            sender="phillip@example.com",
            subject="M Special August date",
            source_date="Tue, 09 Jun 2026 10:00:00 -0700",
        )

        self.assertEqual(receipt["phase"], "Intake Phase")
        self.assertEqual(receipt["source"]["sender"], "phillip@example.com")
        self.assertEqual(receipt["source"]["subject"], "M Special August date")
        self.assertEqual(receipt["request"]["venue"], "M Special")
        self.assertEqual(receipt["request"]["date"], "2026-08-15")
        self.assertEqual(receipt["next_step"], "Mike reviews the request and decides whether to add it to the calendar.")
        self.assertFalse(receipt["protected_writes"]["calendar_updated"])

    def test_receipt_filename_is_stable_and_filesystem_safe(self):
        name = receipt_filename("M Special", "2026-08-15", "M Special August date")

        self.assertEqual(name, "2026-08-15-m-special-m-special-august-date.json")

    def test_write_intake_receipt_creates_json_file(self):
        receipt = build_intake_receipt(
            email_text="Can we book Leashless next Saturday at 6pm in Ventura?",
            sender="venue@example.com",
            subject="Possible Leashless date",
            source_date="Tue, 09 Jun 2026 10:00:00 -0700",
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = write_intake_receipt(receipt, Path(tmp))

            self.assertTrue(path.exists())
            self.assertEqual(path.parent, Path(tmp))
            self.assertIn("leashless", path.name)


if __name__ == "__main__":
    unittest.main()
