import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.neon_health_check import run_health_checks


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
                "bandsheet": passing("bandsheet"),
                "website": passing("website"),
            }
        )

        self.assertEqual(calls, ["bandsheet", "website"])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["successful_lanes"], 2)
        self.assertEqual(result["blocked_lanes"], 0)
        self.assertEqual(result["protected_writes_performed"], 0)

    def test_blocked_lane_does_not_stop_remaining_lanes(self):
        calls = []

        def blocked():
            calls.append("bandsheet")
            return {"status": "blocked", "code": "BANDSHEET_FETCH_FAILED"}

        def passing():
            calls.append("website")
            return {"status": "success"}

        result = run_health_checks(
            {"bandsheet": blocked, "website": passing}
        )

        self.assertEqual(calls, ["bandsheet", "website"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blocked_lanes"], 1)
        self.assertEqual(result["needs_review_lanes"], 0)
        self.assertEqual(result["lanes"]["website"]["status"], "success")

    def test_needs_review_makes_overall_status_needs_review(self):
        def needs_review():
            return {"status": "needs_review", "code": "WEBSITE_MISMATCH"}

        def passing():
            return {"status": "success"}

        result = run_health_checks(
            {"website": needs_review, "bandsheet": passing}
        )

        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["code"], "HEALTH_CHECKS_NEED_REVIEW")
        self.assertEqual(result["blocked_lanes"], 0)
        self.assertEqual(result["needs_review_lanes"], 1)
        self.assertEqual(result["successful_lanes"], 1)

    def test_exception_is_converted_to_isolated_blocked_receipt(self):
        def broken():
            raise RuntimeError("network unavailable")

        result = run_health_checks(
            {
                "website": broken,
                "bandsheet": lambda: {"status": "success"},
            }
        )

        self.assertEqual(result["lanes"]["website"]["status"], "blocked")
        self.assertEqual(
            result["lanes"]["website"]["code"], "HEALTH_CHECK_EXCEPTION"
        )
        self.assertIn("network unavailable", result["lanes"]["website"]["error"])
        self.assertEqual(result["lanes"]["bandsheet"]["status"], "success")

    def test_receipt_does_not_contain_secret_shaped_fields(self):
        result = run_health_checks(
            {
                "bandsheet": lambda: {
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
