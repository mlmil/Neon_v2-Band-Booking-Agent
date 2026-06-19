import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

# We will import these from dashboard_server later when we implement them
from scripts.dashboard_server import (
    get_intake_receipts,
    get_groupme_activity,
    get_venue_folders,
    get_scout_leads,
    get_agentmail_threads,
    get_agentmail_thread_detail
)
from unittest.mock import patch

class TestDashboardAggregators(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)

        self.intake_dir = self.base_dir / "intake" / "receipts"
        self.intake_dir.mkdir(parents=True)

        self.groupme_path = self.base_dir / "groupme" / "groupme_db.json"
        self.groupme_path.parent.mkdir(parents=True)

        self.venues_dir = self.base_dir / "Venues"
        self.venues_dir.mkdir(parents=True)

        self.scout_path = self.base_dir / "scout-leads.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_intake_receipts(self):
        # Create a mock receipt
        receipt = {
            "created_at": "2026-06-10T21:57:49Z",
            "status": "needs_info",
            "source": {
                "sender": "test@example.com",
                "subject": "Booking Request",
                "date": "2026-06-10"
            },
            "request": {
                "venue": "Test Venue",
                "date": "2026-07-01",
                "time": "20:00",
                "city": "Ventura",
                "missing_fields": ["pay"]
            },
            "next_step": "Ask for pay",
            "acknowledgment_draft": "Draft text"
        }
        with open(self.intake_dir / "receipt1.json", "w") as f:
            json.dump(receipt, f)

        # Add a non-actionable receipt
        receipt_ignored = {"status": "ignored"}
        with open(self.intake_dir / "receipt2.json", "w") as f:
            json.dump(receipt_ignored, f)

        data = get_intake_receipts(self.intake_dir)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["venue"], "Test Venue")
        self.assertEqual(data[0]["status"], "needs_review")  # Map 'needs_info' to 'needs_review' or similar
        self.assertEqual(data[0]["missing"], ["pay"])
        self.assertNotIn("Draft text", data[0].get("raw_body", ""))

    def test_get_groupme_activity(self):
        db = {
            "messages": {
                "msg1": {"id": "msg1", "group_name": "Neon Blonde", "sender_id": "system", "text": "Mike joined", "created_at": 1763526352, "name": "System"},
                "msg2": {"id": "msg2", "group_name": "Neon Blonde", "sender_id": "123", "text": "This is an operational message about the gig", "created_at": 1763526353, "name": "Mike"},
                "msg3": {"id": "msg3", "group_name": "Random Group", "sender_id": "123", "text": "Not neon blonde", "created_at": 1763526354, "name": "Mike"}
            }
        }
        with open(self.groupme_path, "w") as f:
            json.dump(db, f)

        data = get_groupme_activity(self.groupme_path)
        # Should filter system messages and non-operational groups
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "msg2")
        self.assertEqual(data[0]["group"], "Neon Blonde")

    def test_get_venue_folders(self):
        v1 = self.venues_dir / "Venue 1" / "Venue 1 - 2026-07-01"
        v1.mkdir(parents=True)
        (v1 / "LOCAL_GIG_RECEIPT.md").touch()
        (v1 / "LOCAL_MODEL_DIGEST.md").touch()

        v2 = self.venues_dir / "Venue 2" / "Venue 2 - 2026-08-01"
        v2.mkdir(parents=True)
        (v2 / "LOCAL_GIG_RECEIPT.md").touch()

        data = get_venue_folders(self.venues_dir)
        self.assertEqual(len(data), 2)
        v1_data = next(d for d in data if d["venue"] == "Venue 1")
        self.assertTrue(v1_data["receipt"])
        self.assertTrue(v1_data["digest"])

        v2_data = next(d for d in data if d["venue"] == "Venue 2")
        self.assertTrue(v2_data["receipt"])
        self.assertFalse(v2_data["digest"])
        self.assertEqual(v2_data["status"], "needs_review")

    @patch("scripts.dashboard_server.agentmail_request")
    def test_get_agentmail_threads(self, mock_req):
        # Mock API response for threads
        mock_req.return_value = (200, {
            "threads": [
                {
                    "thread_id": "thread-123",
                    "subject": "Booking Request",
                    "senders": ["Neon Blonde <neon_blonde@agentmail.to>"],
                    "recipients": ["client@example.com"],
                    "timestamp": "2026-06-10T22:12:29.508Z",
                    "preview": "This is a preview...",
                    "message_count": 2,
                    "labels": ["sent"]
                },
                {
                    "thread_id": "thread-456",
                    "subject": "Gig offer",
                    "senders": ["client2@example.com"],
                    "recipients": ["Neon Blonde <neon_blonde@agentmail.to>"],
                    "timestamp": "2026-06-10T20:12:29.508Z",
                    "preview": "Can you play...",
                    "message_count": 1,
                    "labels": ["received", "unread"]
                }
            ]
        })

        threads = get_agentmail_threads("fake-key")
        self.assertEqual(len(threads), 2)

        t1 = threads[0]
        self.assertEqual(t1["thread_id"], "thread-123")
        self.assertEqual(t1["subject"], "Booking Request")
        self.assertEqual(t1["status"], "Waiting") # Outbound, sent label -> Waiting

        t2 = threads[1]
        self.assertEqual(t2["subject"], "Gig offer")
        self.assertEqual(t2["status"], "Needs reply") # Inbound, unread -> Needs reply

        # Verify secrets and full bodies aren't leaked in this list
        self.assertNotIn("text", t1)
        self.assertNotIn("body", t1)

    @patch("scripts.dashboard_server.agentmail_request")
    def test_get_agentmail_thread_detail(self, mock_req):
        # Mock API response for single thread and its messages
        mock_req.return_value = (200, {
            "thread_id": "thread-123",
            "messages": [
                {
                    "message_id": "msg-1",
                    "timestamp": "2026-06-10T22:12:29Z",
                    "from": "client@example.com",
                    "extracted_text": "How much for the gig?",
                    "text": "Fallback text if extracted missing"
                },
                {
                    "message_id": "msg-2",
                    "timestamp": "2026-06-10T22:15:29Z",
                    "from": "Neon Blonde <neon_blonde@agentmail.to>",
                    "text": "We charge $500."
                }
            ]
        })

        detail = get_agentmail_thread_detail("fake-key", "thread-123")
        self.assertEqual(len(detail["messages"]), 2)
        self.assertEqual(detail["messages"][0]["text"], "How much for the gig?")
        self.assertEqual(detail["messages"][1]["text"], "We charge $500.")
        self.assertEqual(detail["messages"][0]["sender"], "client@example.com")
        self.assertNotIn("api_key", str(detail).lower())

if __name__ == "__main__":
    unittest.main()
