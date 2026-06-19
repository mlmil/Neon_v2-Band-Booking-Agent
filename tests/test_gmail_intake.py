import unittest
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.intake_email_parser import parse_booking_request
from scripts.intake_receipt_tool import build_intake_receipt, write_intake_receipt

class TestGmailIntake(unittest.TestCase):
    def test_booking_detection_and_secret_redaction(self):
        # Email with booking info and a secret (e.g., password)
        email_text = "Can we book Tony's Pizza on July 14th at 8pm in Ventura? My password is secret_123."

        parsed = parse_booking_request(email_text, current_year=2026)

        self.assertEqual(parsed["venue"], "Tony's Pizza")
        self.assertEqual(parsed["city"], "Ventura")
        self.assertIn("07-14", parsed["date"])
        self.assertEqual(parsed["time"], "8pm")

        # Test secret redaction (gap: it currently doesn't redact)
        receipt = build_intake_receipt(
            email_text=email_text,
            sender="test@example.com",
            subject="Booking inquiry",
            source_date="2026-06-10"
        )

        # Since there's no redaction, the acknowledgment draft might not contain it,
        # but if we add previews or full text to receipts, it would leak.
        # Currently, email_text isn't saved in the receipt, which is good for secrets,
        # but bad if we need context. Wait, the parser doesn't save the body!
        self.assertNotIn("secret_123", json.dumps(receipt))

    def test_malformed_message_handling(self):
        email_text = ""  # Empty body
        parsed = parse_booking_request(email_text)

        self.assertEqual(parsed["status"], "needs_info")
        self.assertEqual(len(parsed["missing_fields"]), 4)

    def test_receipt_writing_to_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            receipt = build_intake_receipt(
                email_text="Book us at Bombay in Ventura next Friday at 9pm.",
                sender="vip@rockstarentertainment.com",
                subject="New gig",
                source_date="2026-06-10"
            )

            written_path = write_intake_receipt(receipt, tmp_path)
            self.assertTrue(written_path.exists())

            with open(written_path, 'r') as f:
                saved = json.load(f)
                self.assertEqual(saved["source"]["sender"], "vip@rockstarentertainment.com")

if __name__ == "__main__":
    unittest.main()
