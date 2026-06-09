import unittest

from scripts.intake_email_parser import parse_booking_request


class IntakeEmailParserTests(unittest.TestCase):
    def test_extracts_complete_booking_request(self):
        result = parse_booking_request(
            "Hey, we just looked at the band sheet and you guys are free on "
            "August 15. Can we book M Special at 7pm in Goleta?"
        )

        self.assertEqual(result["status"], "ready_for_mike_review")
        self.assertEqual(result["venue"], "M Special")
        self.assertEqual(result["date"], "2026-08-15")
        self.assertEqual(result["time"], "7pm")
        self.assertEqual(result["city"], "Goleta")
        self.assertEqual(result["missing_fields"], [])

    def test_marks_missing_city_as_needs_info(self):
        result = parse_booking_request("Can we book Ms Special on August 15 at 7pm?")

        self.assertEqual(result["status"], "needs_info")
        self.assertEqual(result["venue"], "Ms Special")
        self.assertEqual(result["date"], "2026-08-15")
        self.assertIn("city", result["missing_fields"])

    def test_flags_relative_dates_for_human_review(self):
        result = parse_booking_request("Can we book Leashless next Saturday at 6pm in Ventura?")

        self.assertEqual(result["status"], "needs_info")
        self.assertIn("date", result["missing_fields"])
        self.assertIn("RELATIVE_DATE_REVIEW", result["review_flags"])

    def test_creates_acknowledgment_draft_in_agent_voice(self):
        result = parse_booking_request("Can we book M Special on August 15 at 7pm in Goleta?")

        self.assertIn("automated AI assistant", result["acknowledgment_draft"])
        self.assertIn("Mike will review the date", result["acknowledgment_draft"])
        self.assertTrue(result["acknowledgment_draft"].endswith("- Neon V2"))


if __name__ == "__main__":
    unittest.main()
