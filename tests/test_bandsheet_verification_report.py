import unittest

from scripts.bandsheet_verification_report import (
    compare_gigs,
    parse_bandsheet_gig,
    parse_calendar_ics,
)


class BandSheetVerificationReportTests(unittest.TestCase):
    def test_matching_gigs_pass(self):
        calendar = [{"date": "2026-06-06", "venue": "Tony's Pizza", "city": "Ventura", "time": "7pm"}]
        bandsheet = [{"date": "2026-06-06", "venue": "Tonys Pizza", "city": "Ventura", "time": "7pm"}]
        result = compare_gigs(calendar, bandsheet)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mismatches"], [])

    def test_minor_venue_expansion_matches_on_same_date(self):
        calendar = [{"date": "2026-06-13", "venue": "Fess Parker", "city": "Los Olivos", "time": "3pm"}]
        bandsheet = [{"date": "2026-06-13", "venue": "Fess Parker Winery", "city": "Los Olivos", "time": "3pm"}]
        result = compare_gigs(calendar, bandsheet)
        self.assertEqual(result["status"], "success")

    def test_missing_bandsheet_gig_blocks_publish(self):
        calendar = [{"date": "2026-06-06", "venue": "Tony's Pizza", "city": "Ventura", "time": "7pm"}]
        bandsheet = []
        result = compare_gigs(calendar, bandsheet)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "BANDSHEET_MISMATCH")

    def test_parse_bandsheet_gig_string(self):
        gig = parse_bandsheet_gig("SAT 8-15-2026 @7PM — Ms Special, Goleta")
        self.assertEqual(
            gig,
            {"date": "2026-08-15", "venue": "Ms Special", "city": "Goleta", "time": "7pm"},
        )

    def test_parse_calendar_ics_gig_with_city_only_location(self):
        ics = (
            """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260816T020000Z
DTEND:20260816T040000Z
LOCATION:Goleta
SUMMARY:Ms Special """
            + """
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260709
DTEND;VALUE=DATE:20260713
SUMMARY:Kyle OUT
END:VEVENT
END:VCALENDAR
"""
        )
        gigs = parse_calendar_ics(ics)
        self.assertEqual(
            gigs,
            [{"date": "2026-08-15", "venue": "Ms Special", "city": "Goleta", "time": "7pm"}],
        )


if __name__ == "__main__":
    unittest.main()
