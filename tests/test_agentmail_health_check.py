import unittest

from scripts.agentmail_health_check import (
    fingerprint_key,
    parse_inbox_emails,
    summarize_list_inboxes_result,
)


class AgentMailHealthCheckTests(unittest.TestCase):
    def test_fingerprint_key_does_not_expose_secret(self):
        result = fingerprint_key("am_us_example_secret")
        self.assertEqual(result["present"], True)
        self.assertEqual(result["length"], 20)
        self.assertNotIn("am_us_example_secret", str(result))

    def test_parse_inbox_emails_handles_agentmail_response_shape(self):
        body = {
            "count": 2,
            "inboxes": [
                {"email": "neon_blonde@agentmail.to"},
                {"email": "blue_rose@agentmail.to"},
            ],
        }
        self.assertEqual(
            parse_inbox_emails(body),
            ["neon_blonde@agentmail.to", "blue_rose@agentmail.to"],
        )

    def test_summarize_list_inboxes_blocks_missing_neon_inbox(self):
        result = summarize_list_inboxes_result(
            http_status=200,
            body={"count": 1, "inboxes": [{"email": "blue_rose@agentmail.to"}]},
            required_inbox="neon_blonde@agentmail.to",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "AGENTMAIL_INBOX_MISSING")


if __name__ == "__main__":
    unittest.main()
