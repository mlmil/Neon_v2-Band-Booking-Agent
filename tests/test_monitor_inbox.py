import tempfile
import unittest
from pathlib import Path

from scripts.monitor_inbox import build_flagged_email, create_intake_receipts_for_flagged


class MonitorInboxTests(unittest.TestCase):
    def test_build_flagged_email_detects_booking_keyword(self):
        flagged = build_flagged_email(
            sender="Phillip <phillip@example.com>",
            subject="M Special August date",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Can we book M Special on August 15 at 7pm in Goleta?",
            message_id="<msg-1>",
        )

        self.assertIsNotNone(flagged)
        self.assertFalse(flagged["vip"])
        self.assertEqual(flagged["message_id"], "<msg-1>")
        self.assertIn("Can we book", flagged["body"])

    def test_build_flagged_email_ignores_non_actionable_message(self):
        flagged = build_flagged_email(
            sender="Newsletter <news@example.com>",
            subject="Weekly specials",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Here are this week's food specials.",
        )

        self.assertIsNone(flagged)

    def test_create_intake_receipts_for_flagged_writes_local_receipt(self):
        flagged = build_flagged_email(
            sender="Phillip <phillip@example.com>",
            subject="M Special August date",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Can we book M Special on August 15 at 7pm in Goleta?",
            message_id="<msg-1>",
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = create_intake_receipts_for_flagged([flagged], Path(tmp))

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].exists())
            self.assertIn("m-special", paths[0].name)


if __name__ == "__main__":
    unittest.main()
