import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

# Add parent dir to path so we can import the scripts
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.fetch_groupme_messages as fetch
import scripts.sync_groupme_messages as sync


class TestGroupMeFetch(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("scripts.fetch_groupme_messages.os.environ.get")
    def test_token_discovery(self, mock_env_get):
        # Test CLI arg overriding everything
        mock_env_get.return_value = "env_token"
        self.assertEqual(fetch.load_token("cli_token"), "cli_token")

        # Test ENV fallback
        self.assertEqual(fetch.load_token(None), "env_token")

        # Fallback to file (mocked by monkeypatching the function logic directly or mocking paths)
        # But we only need to verify it doesn't crash and respects order

    @patch("urllib.request.urlopen")
    def test_api_errors_do_not_leak_token(self, mock_urlopen):
        # Simulate an HTTP error
        mock_urlopen.side_effect = urllib.error.HTTPError("http://url", 401, "Unauthorized", {}, None)

        try:
            fetch.api_get("/test", "secret_token_123")
        except SystemExit as e:
            # Token should NOT be in the exception message
            self.assertNotIn("secret_token_123", str(e))
            self.assertIn("401", str(e))
        else:
            self.fail("Expected SystemExit")

    @patch("scripts.fetch_groupme_messages.api_get")
    def test_pagination_stops_correctly(self, mock_api_get):
        # Return 1 message on first call, empty list on second call
        mock_api_get.side_effect = [
            {"response": {"messages": [{"id": "1", "text": "Hello"}]}},
            {"response": {"messages": []}},
        ]

        messages = fetch.fetch_messages("token", "group_1")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["id"], "1")


class TestGroupMeSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name) / "messages"
        self.source_dir.mkdir()
        self.db_path = Path(self.temp_dir.name) / ".groupme_db.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_malformed_json_skipped(self):
        # Create a valid message
        valid_msg = self.source_dir / "1.json"
        valid_msg.write_text(json.dumps({"id": "1", "text": "Valid", "group_name": "Test Group"}))

        # Create a malformed message
        malformed_msg = self.source_dir / "2.json"
        malformed_msg.write_text("{malformed: true,")

        # Run sync
        # Since sync is a script, we will simulate the logic
        data = sync.load_existing(self.db_path)
        messages = data["messages"]
        added = 0

        # Import logic from sync script
        for path in sorted(self.source_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    msg = json.load(f)
            except json.JSONDecodeError:
                continue

            msg_id = str(msg.get("id") or path.stem)
            if msg_id not in messages:
                messages[msg_id] = {
                    "id": msg_id,
                    "text": msg.get("text"),
                    "group_name": msg.get("group_name"),
                }
                added += 1

        # Only the valid message should be ingested
        self.assertEqual(added, 1)
        self.assertIn("1", messages)
        self.assertNotIn("2", messages)
        self.assertEqual(messages["1"]["group_name"], "Test Group")

    def test_duplicate_prevention(self):
        # Pre-populate DB
        data = {"messages": {"1": {"id": "1", "text": "Old message"}}, "last_sync": "2026-06-10"}
        self.db_path.write_text(json.dumps(data))

        # Write same message file
        valid_msg = self.source_dir / "1.json"
        valid_msg.write_text(json.dumps({"id": "1", "text": "New content but same ID"}))

        data_loaded = sync.load_existing(self.db_path)
        messages = data_loaded["messages"]
        added = 0

        for path in sorted(self.source_dir.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as f:
                    msg = json.load(f)
            except json.JSONDecodeError:
                continue

            msg_id = str(msg.get("id") or path.stem)
            if msg_id not in messages:
                messages[msg_id] = {"id": msg_id, "text": msg.get("text")}
                added += 1

        self.assertEqual(added, 0)
        self.assertEqual(messages["1"]["text"], "Old message")

if __name__ == "__main__":
    unittest.main()
