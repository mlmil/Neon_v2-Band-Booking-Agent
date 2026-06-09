import tempfile
import unittest
from pathlib import Path

from scripts.venue_agent_tool import (
    CalendarEvent,
    build_folder_plan,
    is_test_venue,
    normalize_venue_name,
    validate_calendar_event,
)


class VenueAgentToolTests(unittest.TestCase):
    def test_calendar_event_accepts_city_only_location(self):
        event = CalendarEvent(title="Tonys Pizza", location="Ventura", start="2026-06-06T19:00:00")
        result = validate_calendar_event(event)
        self.assertEqual(result["status"], "success")

    def test_calendar_event_blocks_full_address_location(self):
        event = CalendarEvent(
            title="Tonys Pizza",
            location="Ventura, California, United States",
            start="2026-06-06T19:00:00",
        )
        result = validate_calendar_event(event)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "BLOCKED_CALENDAR")

    def test_normalize_venue_name_handles_punctuation(self):
        self.assertEqual(normalize_venue_name("Harry's Night Club"), "harrys night club")

    def test_test_venue_aliases_include_both_spellings(self):
        self.assertTrue(is_test_venue("Club Babaloo"))
        self.assertTrue(is_test_venue("club Bobaloo"))

    def test_build_folder_plan_uses_existing_venue_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tonys Pizza").mkdir()
            event = CalendarEvent("Tony's Pizza", "Ventura", "2026-06-06T19:00:00")
            plan = build_folder_plan(event, root)
            self.assertEqual(plan["status"], "success")
            self.assertEqual(plan["venue_folder"], str(root / "Tonys Pizza"))
            self.assertEqual(plan["gig_folder"], str(root / "Tonys Pizza" / "gigs" / "2026-06-06"))

    def test_build_folder_plan_handles_city_only_location_and_title_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Ms special").mkdir()
            event = CalendarEvent("Ms Special ", "Goleta", "2026-08-15T19:00:00-07:00")
            plan = build_folder_plan(event, root)
            self.assertEqual(plan["status"], "success")
            self.assertEqual(plan["venue_folder"], str(root / "Ms special"))
            self.assertEqual(plan["gig_folder"], str(root / "Ms special" / "gigs" / "2026-08-15"))

    def test_build_folder_plan_marks_club_babaloo_as_test_venue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = CalendarEvent("Club Bobaloo", "Ventura", "2026-08-15T19:00:00-07:00")
            plan = build_folder_plan(event, root)
            self.assertEqual(plan["status"], "success")
            self.assertEqual(plan["code"], "TEST_VENUE")
            self.assertTrue(plan["is_test_venue"])
            self.assertEqual(plan["venue_folder"], str(root / "_Test Venues" / "Club Babaloo"))

    def test_build_folder_plan_flags_weekday_gig_for_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = CalendarEvent("Club Babaloo", "Bakersfield", "2026-10-07T19:00:00-07:00")
            plan = build_folder_plan(event, root)
            self.assertEqual(plan["status"], "success")
            self.assertEqual(plan["code"], "TEST_VENUE")
            self.assertEqual(plan["warnings"][0]["code"], "WEEKDAY_GIG_REVIEW")

    def test_build_folder_plan_flags_early_santa_barbara_weekday_logistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = CalendarEvent("Club Babaloo", "Goleta", "2026-10-09T18:00:00-07:00")
            plan = build_folder_plan(event, root)
            warning_codes = {warning["code"] for warning in plan["warnings"]}
            self.assertIn("SB_EARLY_WEEKDAY_LOGISTICS", warning_codes)


if __name__ == "__main__":
    unittest.main()
