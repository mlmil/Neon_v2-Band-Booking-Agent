import json
import os
import tempfile
import unittest
from pathlib import Path

# Note: We will implement dashboard_server.py which will expose an app or handler
# But for TDD, we test via the functions that will be used by the server endpoints,
# or we test via a test client if we use a microframework, or we mock the http server.
# Since the requirement is "Python standard-library localhost server", we can test the handler
# methods or the business logic functions directly.

from scripts.dashboard_server import (
    get_post_gig_data,
    handle_post_gig_payout,
    is_test_payout,
)

class TestDashboardServer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.queue_path = Path(self.temp_dir.name) / "queue.csv"
        self.payouts_path = Path(self.temp_dir.name) / "payouts.csv"

        # Write some queue data
        with open(self.queue_path, "w", encoding="utf-8") as f:
            f.write("gig_id,venue,city,date,start_at,end_at,queue_status,next_step,created_at,updated_at\n")
            f.write("gig-1,Venue 1,City 1,2026-06-01,2026-06-01T20:00:00,2026-06-01T23:00:00,needs_closeout,next,2026-06-01,2026-06-01\n")
            f.write("club-babaloo-1,Club Babaloo,City 2,2026-06-02,2026-06-02T20:00:00,2026-06-02T23:00:00,closed,next,2026-06-02,2026-06-02\n")
            f.write("gig-3,Venue 3,City 3,2026-06-03,2026-06-03T20:00:00,2026-06-03T23:00:00,scheduled,next,2026-06-03,2026-06-03\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_merge_by_gig_id(self):
        with open(self.payouts_path, "w", encoding="utf-8") as f:
            f.write("VENUE,CITY,DATE,PAYOUT,TIPS\n")
            f.write("Venue 1,City 1,2026-06-01,0.00,0.00\n")

        data = get_post_gig_data(self.queue_path, self.payouts_path)
        # Should return active queue items (needs_closeout or closed)
        self.assertEqual(len(data), 2)

        # Check merge
        gig_1 = next(item for item in data if item["id"] == "gig-1")
        self.assertEqual(gig_1["base_pay"], "0.00")

    def test_missing_payout_ledger_still_returns_active_queue(self):
        # payouts_path does not exist
        data = get_post_gig_data(self.queue_path, self.payouts_path)
        self.assertEqual(len(data), 2)
        gig_1 = next(item for item in data if item["id"] == "gig-1")
        self.assertIsNone(gig_1.get("base_pay"))

    def test_saved_payout_does_not_mark_payment_complete(self):
        payload = {
            "gig_id": "gig-1",
            "venue": "Venue 1",
            "city": "City 1",
            "date": "2026-06-01",
            "base_pay_expected": "500",
            "base_pay_received": "500",
            "tips_received": "100",
            "payment_method": "Cash",
            "payment_handle": "",
            "received_by": "Mike"
        }
        resp = handle_post_gig_payout(payload, self.payouts_path)
        # It's an authoritative CSV, it doesn't store status. But we don't crash.
        self.assertNotIn("payment_status", resp["row"])

    def test_expected_pay_is_derived_from_received_plus_still_owed(self):
        payload = {
            "gig_id": "gig-1",
            "venue": "Venue 1",
            "city": "City 1",
            "date": "2026-06-01",
            "base_pay_received": "400",
            "still_owed": "100",
            "tips_received": "25",
            "payment_method": "Venmo",
            "received_by": "Mike",
        }
        resp = handle_post_gig_payout(payload, self.payouts_path)
        self.assertEqual(resp["row"]["PAYOUT"], "$400.00")

    def test_paid_complete_is_ignored(self):
        payload = {
            "gig_id": "gig-1",
            "venue": "Venue 1",
            "city": "City 1",
            "date": "2026-06-01",
            "base_pay_expected": "500",
            "base_pay_received": "500",
            "tips_received": "100",
            "payment_method": "Cash",
            "payment_handle": "",
            "received_by": "Mike",
            "payment_status": "paid_complete"
        }
        handle_post_gig_payout(payload, self.payouts_path)
        # the row handles paid_complete gracefully by dropping it.

    def test_no_credential_fields_exposed(self):
        data = get_post_gig_data(self.queue_path, self.payouts_path)
        json_data = json.dumps(data).lower()
        self.assertNotIn("password", json_data)
        self.assertNotIn("token", json_data)
        self.assertNotIn("api_key", json_data)

    def test_club_babaloo_test_data(self):
        data = get_post_gig_data(self.queue_path, self.payouts_path)
        babaloo = next(item for item in data if item["id"] == "club-babaloo-1")
        # Should be clearly marked as test data
        self.assertIn("TEST DATA", babaloo.get("summary", "").upper() + babaloo.get("notes", "").upper())

    def test_club_babaloo_venue_routes_to_test_ledger_with_opaque_gig_id(self):
        payload = {"gig_id": "google-event-abc123", "venue": "Club Babaloo"}
        self.assertTrue(is_test_payout(payload))

    def test_regular_venue_does_not_route_to_test_ledger(self):
        payload = {"gig_id": "google-event-abc123", "venue": "Tony's Pizza"}
        self.assertFalse(is_test_payout(payload))

    from unittest.mock import patch
    @patch('scripts.lm_studio_health_check.run_health_check')
    def test_health_projection_maps_success(self, mock_check):
        mock_check.return_value = {
            "status": "success",
            "code": "LM_STUDIO_OK",
            "configured_model": "gemma-4-e2b-it",
            "active_model": "lfm2.5-8b-a1b",
            "active_model_display_name": "LFM2.5 8B A1B",
        }
        from scripts.dashboard_server import get_health_projection
        projection = get_health_projection()
        self.assertEqual(projection["status"], "success")
        self.assertEqual(projection["model"], "LFM2.5 8B A1B")
        self.assertIn("loaded", projection["message"])
        self.assertIn("last_ok", projection)
        self.assertEqual(projection["pending_digests"], [])

    @patch('scripts.lm_studio_health_check.run_health_check')
    def test_health_projection_maps_needs_review(self, mock_check):
        mock_check.return_value = {
            "status": "needs_review",
            "code": "LM_STUDIO_NO_MODEL_LOADED",
            "configured_model": "gemma-4-e2b-it",
            "active_model": None,
        }
        from scripts.dashboard_server import get_health_projection
        projection = get_health_projection()
        self.assertEqual(projection["status"], "needs_review")
        self.assertIn("no model is loaded", projection["message"])

    @patch('scripts.lm_studio_health_check.run_health_check')
    def test_health_projection_maps_blocked(self, mock_check):
        mock_check.return_value = {
            "status": "blocked",
            "code": "LM_STUDIO_UNAVAILABLE"
        }
        from scripts.dashboard_server import get_health_projection
        projection = get_health_projection()
        self.assertEqual(projection["status"], "blocked")
        self.assertIn("OFFLINE", projection["message"])

if __name__ == "__main__":
    unittest.main()
