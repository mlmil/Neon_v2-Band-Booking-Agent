import json
import tempfile
import unittest
from pathlib import Path

from scripts.agent_compatibility_check import (
    check_credential,
    run_club_babaloo_fixture,
    run_compatibility_check,
)


class AgentCompatibilityCheckTests(unittest.TestCase):
    def test_environment_credential_is_reported_without_exposing_value(self):
        secret = "top-secret-test-value"
        result = check_credential(
            {
                "id": "agentmail",
                "required": True,
                "sources": [{"type": "env", "name": "AGENTMAIL_API_KEY"}],
            },
            environ={"AGENTMAIL_API_KEY": secret},
        )

        serialized = json.dumps(result)
        self.assertEqual(result["status"], "available")
        self.assertNotIn(secret, serialized)

    def test_missing_required_credential_blocks_full_operator_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "credentials": [
                            {
                                "id": "missing-service",
                                "required": True,
                                "sources": [{"type": "env", "name": "MISSING_SERVICE_KEY"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_compatibility_check(
                agent="claude",
                manifest_path=manifest,
                environ={},
                run_network=False,
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("missing-service", result["missing_required_credentials"])

    def test_all_agent_profiles_share_the_same_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = Path(temp_dir) / "manifest.json"
            manifest.write_text(json.dumps({"credentials": []}), encoding="utf-8")

            results = [
                run_compatibility_check(
                    agent=agent,
                    manifest_path=manifest,
                    environ={},
                    run_network=False,
                )
                for agent in ("codex", "claude", "hermes")
            ]

        self.assertEqual({result["agent"] for result in results}, {"codex", "claude", "hermes"})
        self.assertTrue(all(result["club_babaloo"]["status"] == "success" for result in results))

    def test_club_babaloo_fixture_is_local_and_approval_gated(self):
        result = run_club_babaloo_fixture()

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_test_venue"])
        self.assertFalse(result["protected_writes"]["calendar_updated"])
        self.assertFalse(result["protected_writes"]["email_sent"])
        self.assertFalse(result["protected_writes"]["payment_completed"])


if __name__ == "__main__":
    unittest.main()
