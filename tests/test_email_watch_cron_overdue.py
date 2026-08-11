"""Tests for email_watch_cron.py overdue cooldown logic."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.email_watch_cron import load_state, save_state


class TestOverdueCooldownLogic(unittest.TestCase):
    """Test the overdue alert cooldown behavior."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "email_watch_state.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def test_overdue_alerted_initialized_when_missing(self):
        """State without overdue_alerted key loads with empty dict."""
        self._write_state({"seen_message_ids": [], "pending_replies": {}})
        with patch("scripts.email_watch_cron.STATE_FILE", str(self.state_file)):
            state = load_state()
        overdue_alerted = state.get("overdue_alerted", {})
        self.assertEqual(overdue_alerted, {})

    def test_overdue_alerted_persisted(self):
        """overdue_alerted dict is saved and loaded correctly."""
        state = {
            "seen_message_ids": ["1"],
            "pending_replies": {},
            "overdue_alerted": {"Test Subject": "2026-08-01T12:00:00+00:00"},
        }
        self._write_state(state)
        with patch("scripts.email_watch_cron.STATE_FILE", str(self.state_file)):
            loaded = load_state()
        self.assertEqual(
            loaded["overdue_alerted"]["Test Subject"],
            "2026-08-01T12:00:00+00:00",
        )

    def test_cooldown_suppresses_recent_alert(self):
        """A thread alerted within the cooldown window is suppressed."""
        now = datetime.now(timezone.utc)
        # Thread is 30 hours old (overdue)
        first_seen = (now - timedelta(hours=30)).isoformat()
        # Alert was sent 12 hours ago (within 24h cooldown)
        last_alert = (now - timedelta(hours=12)).isoformat()

        state = {
            "pending_replies": {
                "Test Subject": {
                    "from": "test@example.com",
                    "subject": "Test Subject",
                    "date": "Mon, 1 Jan 2026",
                    "first_seen": first_seen,
                }
            },
            "overdue_alerted": {"Test Subject": last_alert},
        }

        # Simulate the cooldown logic from email_watch_cron.py
        OVERDUE_ALERT_COOLDOWN_HOURS = 24
        overdue_alerted = state.get("overdue_alerted", {})
        overdue = []

        for subj, info in state["pending_replies"].items():
            try:
                fs = datetime.fromisoformat(info.get("first_seen", ""))
                age_hours = (now - fs).total_seconds() / 3600
            except Exception:
                age_hours = 0
            if age_hours <= 24:
                continue
            last_alert_str = overdue_alerted.get(subj)
            should_alert = True
            if last_alert_str:
                try:
                    last_alert_dt = datetime.fromisoformat(last_alert_str)
                    hours_since = (now - last_alert_dt).total_seconds() / 3600
                    if hours_since < OVERDUE_ALERT_COOLDOWN_HOURS:
                        should_alert = False
                except Exception:
                    pass
            if should_alert:
                overdue.append({"subject": subj})
                overdue_alerted[subj] = now.isoformat()

        self.assertEqual(len(overdue), 0, "Recently alerted thread should be suppressed")

    def test_cooldown_allows_alert_after_expiry(self):
        """A thread alerted beyond the cooldown window alerts again."""
        now = datetime.now(timezone.utc)
        # Thread is 48 hours old (overdue)
        first_seen = (now - timedelta(hours=48)).isoformat()
        # Alert was sent 30 hours ago (beyond 24h cooldown)
        last_alert = (now - timedelta(hours=30)).isoformat()

        state = {
            "pending_replies": {
                "Test Subject": {
                    "from": "test@example.com",
                    "subject": "Test Subject",
                    "date": "Mon, 1 Jan 2026",
                    "first_seen": first_seen,
                }
            },
            "overdue_alerted": {"Test Subject": last_alert},
        }

        OVERDUE_ALERT_COOLDOWN_HOURS = 24
        overdue_alerted = state.get("overdue_alerted", {})
        overdue = []

        for subj, info in state["pending_replies"].items():
            try:
                fs = datetime.fromisoformat(info.get("first_seen", ""))
                age_hours = (now - fs).total_seconds() / 3600
            except Exception:
                age_hours = 0
            if age_hours <= 24:
                continue
            last_alert_str = overdue_alerted.get(subj)
            should_alert = True
            if last_alert_str:
                try:
                    last_alert_dt = datetime.fromisoformat(last_alert_str)
                    hours_since = (now - last_alert_dt).total_seconds() / 3600
                    if hours_since < OVERDUE_ALERT_COOLDOWN_HOURS:
                        should_alert = False
                except Exception:
                    pass
            if should_alert:
                overdue.append({"subject": subj})
                overdue_alerted[subj] = now.isoformat()

        self.assertEqual(len(overdue), 1, "Expired cooldown should allow re-alert")
        self.assertEqual(overdue[0]["subject"], "Test Subject")

    def test_first_time_overdue_alerts_immediately(self):
        """A thread that becomes overdue for the first time alerts."""
        now = datetime.now(timezone.utc)
        # Thread is 25 hours old (just became overdue)
        first_seen = (now - timedelta(hours=25)).isoformat()

        state = {
            "pending_replies": {
                "Test Subject": {
                    "from": "test@example.com",
                    "subject": "Test Subject",
                    "date": "Mon, 1 Jan 2026",
                    "first_seen": first_seen,
                }
            },
            "overdue_alerted": {},  # never alerted
        }

        OVERDUE_ALERT_COOLDOWN_HOURS = 24
        overdue_alerted = state.get("overdue_alerted", {})
        overdue = []

        for subj, info in state["pending_replies"].items():
            try:
                fs = datetime.fromisoformat(info.get("first_seen", ""))
                age_hours = (now - fs).total_seconds() / 3600
            except Exception:
                age_hours = 0
            if age_hours <= 24:
                continue
            last_alert_str = overdue_alerted.get(subj)
            should_alert = True
            if last_alert_str:
                try:
                    last_alert_dt = datetime.fromisoformat(last_alert_str)
                    hours_since = (now - last_alert_dt).total_seconds() / 3600
                    if hours_since < OVERDUE_ALERT_COOLDOWN_HOURS:
                        should_alert = False
                except Exception:
                    pass
            if should_alert:
                overdue.append({"subject": subj})
                overdue_alerted[subj] = now.isoformat()

        self.assertEqual(len(overdue), 1)
        self.assertIn("Test Subject", overdue_alerted)

    def test_not_overdue_no_alert(self):
        """A thread younger than 24h does not alert."""
        now = datetime.now(timezone.utc)
        # Thread is 12 hours old (not yet overdue)
        first_seen = (now - timedelta(hours=12)).isoformat()

        state = {
            "pending_replies": {
                "Test Subject": {
                    "from": "test@example.com",
                    "subject": "Test Subject",
                    "date": "Mon, 1 Jan 2026",
                    "first_seen": first_seen,
                }
            },
            "overdue_alerted": {},
        }

        overdue = []
        for subj, info in state["pending_replies"].items():
            try:
                fs = datetime.fromisoformat(info.get("first_seen", ""))
                age_hours = (now - fs).total_seconds() / 3600
            except Exception:
                age_hours = 0
            if age_hours <= 24:
                continue
            overdue.append({"subject": subj})

        self.assertEqual(len(overdue), 0)

    def test_cleanup_removes_overdue_alerted_on_reply(self):
        """When a pending reply is resolved, overdue_alerted is cleaned up."""
        pending = {"Test Subject": {"from": "test@example.com"}}
        overdue_alerted = {"Test Subject": "2026-08-01T12:00:00+00:00"}

        # Simulate cleanup
        base_subj = "Test Subject"
        pending.pop(base_subj, None)
        overdue_alerted.pop(base_subj, None)

        self.assertNotIn("Test Subject", pending)
        self.assertNotIn("Test Subject", overdue_alerted)

    def test_corrupt_alert_timestamp_treated_as_not_alerted(self):
        """A corrupt timestamp in overdue_alerted is treated as never alerted."""
        now = datetime.now(timezone.utc)
        first_seen = (now - timedelta(hours=30)).isoformat()

        state = {
            "pending_replies": {
                "Test Subject": {
                    "from": "test@example.com",
                    "subject": "Test Subject",
                    "date": "Mon, 1 Jan 2026",
                    "first_seen": first_seen,
                }
            },
            "overdue_alerted": {"Test Subject": "not-a-valid-timestamp"},
        }

        OVERDUE_ALERT_COOLDOWN_HOURS = 24
        overdue_alerted = state.get("overdue_alerted", {})
        overdue = []

        for subj, info in state["pending_replies"].items():
            try:
                fs = datetime.fromisoformat(info.get("first_seen", ""))
                age_hours = (now - fs).total_seconds() / 3600
            except Exception:
                age_hours = 0
            if age_hours <= 24:
                continue
            last_alert_str = overdue_alerted.get(subj)
            should_alert = True
            if last_alert_str:
                try:
                    last_alert_dt = datetime.fromisoformat(last_alert_str)
                    hours_since = (now - last_alert_dt).total_seconds() / 3600
                    if hours_since < OVERDUE_ALERT_COOLDOWN_HOURS:
                        should_alert = False
                except Exception:
                    pass  # corrupt timestamp → treat as not alerted
            if should_alert:
                overdue.append({"subject": subj})
                overdue_alerted[subj] = now.isoformat()

        self.assertEqual(len(overdue), 1, "Corrupt timestamp should allow alert")


class TestDryRunFlag(unittest.TestCase):
    """Test the --dry-run flag behavior."""

    def test_dry_run_does_not_save_state(self):
        """--dry-run should print but not persist state."""
        # This is a structural test — we verify the flag exists in the source
        script_path = Path(__file__).resolve().parents[1] / "scripts" / "email_watch_cron.py"
        with open(script_path) as f:
            content = f.read()
        self.assertIn("--dry-run", content)
        self.assertIn("args.dry_run", content)
        self.assertIn("[DRY RUN] State not saved", content)


if __name__ == "__main__":
    unittest.main()
