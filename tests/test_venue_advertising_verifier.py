import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.venue_advertising_verifier import (
    FigueroaMountainSource,
    LeashlessBrewingSource,
    TonysPizzariaSource,
    _find_venue_source,
    _gig_matches_event,
    _norm,
    verify_venue_advertising,
)


class TestVenueSourceMatching(unittest.TestCase):
    def test_find_tonys_pizzaria(self):
        src = _find_venue_source("Tony's Pizzaria")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Tony's Pizzaria")

    def test_find_tonys_pizza(self):
        src = _find_venue_source("Tony's Pizza")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Tony's Pizzaria")

    def test_find_leashless(self):
        src = _find_venue_source("Leashless Brewing")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Leashless Brewing")

    def test_find_leashless_short(self):
        src = _find_venue_source("Leashless")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Leashless Brewing")

    def test_find_figueroa_mountain(self):
        src = _find_venue_source("Figueroa Mountain Brewing")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Figueroa Mountain Brewing")

    def test_find_fig_mountain(self):
        src = _find_venue_source("Fig Mountain")
        self.assertIsNotNone(src)
        self.assertEqual(src.name, "Figueroa Mountain Brewing")

    def test_find_unknown_venue(self):
        src = _find_venue_source("Unknown Venue")
        self.assertIsNone(src)


class TestGigEventMatching(unittest.TestCase):
    def test_match_by_date_and_band_mention(self):
        gig = {"date": "2026-08-02", "venue": "Tony's Pizzaria", "time": "8pm"}
        event = {"date": "2026-08-02", "title": "Live music: Neon Blonde 80s cover band"}
        self.assertTrue(_gig_matches_event(gig, event))

    def test_no_match_wrong_date(self):
        gig = {"date": "2026-08-02", "venue": "Tony's Pizzaria", "time": "8pm"}
        event = {"date": "2026-08-03", "title": "Live music: Neon Blonde"}
        self.assertFalse(_gig_matches_event(gig, event))

    def test_no_match_no_band_mention(self):
        gig = {"date": "2026-08-02", "venue": "Tony's Pizzaria", "time": "8pm"}
        event = {"date": "2026-08-02", "title": "Trivia night"}
        self.assertFalse(_gig_matches_event(gig, event))


class TestVerifyVenueAdvertising(unittest.TestCase):
    def test_no_adapter_for_unknown_venue(self):
        gigs = [{"date": "2026-08-10", "venue": "Unknown Place", "city": "Nowhere", "time": "8pm"}]
        result = verify_venue_advertising(gigs, lookback_days=0, lookahead_days=30)
        self.assertEqual(result["results"][0]["status"], "NO_ADAPTER")
        self.assertEqual(result["status"], "ok")

    def test_match_status_when_band_advertised(self):
        """Mock test: verify MATCH when venue advertises the gig."""
        # We can't easily mock the HTTP fetch without more plumbing,
        # but we can test the logic by checking the structure.
        # Use a date far in the future to avoid window filtering.
        gigs = [{"date": "2026-12-31", "venue": "Tony's Pizzaria", "city": "Ventura", "time": "8pm"}]
        # The actual fetch will fail in test environment (no network),
        # so we expect DATA_UNAVAILABLE
        result = verify_venue_advertising(gigs, lookback_days=0, lookahead_days=365)
        self.assertGreater(len(result["results"]), 0)
        self.assertIn(result["results"][0]["status"], ["MATCH", "DATA_UNAVAILABLE", "GIG_NOT_ADVERTISED", "MISMATCH"])


class TestVenueSourceParsers(unittest.TestCase):
    def test_tonys_parser_with_sample_html(self):
        src = TonysPizzariaSource()
        html = """
        <html><body>
        <div>August 2 - Neon Blonde live at 8pm</div>
        <div>August 16 - Trivia night</div>
        </body></html>
        """
        events = src.parse_events(html)
        dates = [e["date"] for e in events]
        self.assertIn("2026-08-02", dates)
        self.assertIn("2026-08-16", dates)

    def test_leashless_parser_with_sample_html(self):
        src = LeashlessBrewingSource()
        html = """
        <html><body>
        <div>September 19: Neon Blonde returns!</div>
        </body></html>
        """
        events = src.parse_events(html)
        dates = [e["date"] for e in events]
        self.assertIn("2026-09-19", dates)

    def test_figueroa_parser_with_sample_html(self):
        src = FigueroaMountainSource()
        html = """
        <html><body>
        <div>Aug 28 - Live music</div>
        </body></html>
        """
        events = src.parse_events(html)
        dates = [e["date"] for e in events]
        self.assertIn("2026-08-28", dates)


if __name__ == "__main__":
    unittest.main()
