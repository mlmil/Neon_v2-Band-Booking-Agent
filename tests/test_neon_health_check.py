import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.neon_health_check import (
    dashboard_health_check,
    run_health_checks,
)


class TestNeonHealthCheck(unittest.TestCase):
    def test_all_lanes_run_and_success_is_aggregated(self):
        calls = []

        def passing(name):
            def check():
                calls.append(name)
                return {"status": "success", "code": f"{name.upper()}_OK"}

            return check

        result = run_health_checks(
            {
                "agentmail": passing("agentmail"),
                "bandsheet": passing("bandsheet"),
                "website": passing("website"),
                "dashboard": passing("dashboard"),
            }
        )

        self.assertEqual(
            calls, ["agentmail", "bandsheet", "website", "dashboard"]
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["successful_lanes"], 4)
        self.assertEqual(result["blocked_lanes"], 0)
        self.assertEqual(result["protected_writes_performed"], 0)

    def test_blocked_lane_does_not_stop_remaining_lanes(self):
        calls = []

        def blocked():
            calls.append("agentmail")
            return {"status": "blocked", "code": "AGENTMAIL_AUTH_FAILED"}

        def passing():
            calls.append("bandsheet")
            return {"status": "success"}

        result = run_health_checks(
            {"agentmail": blocked, "bandsheet": passing}
        )

        self.assertEqual(calls, ["agentmail", "bandsheet"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blocked_lanes"], 1)
        self.assertEqual(result["lanes"]["bandsheet"]["status"], "success")

    def test_exception_is_converted_to_isolated_blocked_receipt(self):
        def broken():
            raise RuntimeError("network unavailable")

        result = run_health_checks(
            {
                "website": broken,
                "dashboard": lambda: {"status": "success"},
            }
        )

        self.assertEqual(result["lanes"]["website"]["status"], "blocked")
        self.assertEqual(
            result["lanes"]["website"]["code"], "HEALTH_CHECK_EXCEPTION"
        )
        self.assertIn("network unavailable", result["lanes"]["website"]["error"])
        self.assertEqual(result["lanes"]["dashboard"]["status"], "success")

    def test_dashboard_check_requires_static_files_and_loads_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dashboard = root / "dashboard"
            (dashboard / "components").mkdir(parents=True)
            (dashboard / "index.html").write_text("<html></html>")
            (dashboard / "components" / "app.jsx").write_text("function App() {}")
            (dashboard / "components" / "panels.jsx").write_text(
                "function Panels() {}"
            )
            queue = root / "queue.csv"
            queue.write_text(
                "gig_id,venue,city,date,start_at,end_at,queue_status,next_step,"
                "created_at,updated_at\n"
                "gig-1,Venue,City,2026-06-01,,,needs_closeout,enter payout,,\n"
            )

            result = dashboard_health_check(
                dashboard_dir=dashboard,
                queue_path=queue,
                payouts_path=root / "missing-payouts.csv",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["active_post_gig_items"], 1)

    def test_receipt_does_not_contain_secret_shaped_fields(self):
        result = run_health_checks(
            {
                "agentmail": lambda: {
                    "status": "success",
                    "key": {"present": True, "sha256_prefix": "abc123"},
                    "api_key": "secret",
                }
            }
        )
        serialized = json.dumps(result).lower()
        self.assertNotIn('"password"', serialized)
        self.assertNotIn('"api_key"', serialized)
        self.assertNotIn('"token"', serialized)
        self.assertNotIn('"key"', serialized)
        self.assertNotIn("abc123", serialized)
        self.assertFalse(result["credential_values_exposed"])

    def test_script_can_be_invoked_directly(self):
        result = subprocess.run(
            [sys.executable, "scripts/neon_health_check.py", "--help"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
