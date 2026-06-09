import unittest

from scripts.agentmail_send import build_fallback_draft, build_send_payload, summarize_send_result


class AgentMailSendTests(unittest.TestCase):
    def test_build_send_payload_requires_agent_signature(self):
        payload = build_send_payload(
            to=["alfred@example.com"],
            cc=["neon@example.com"],
            subject="Cruisery flyers",
            text="The flyers are ready.",
        )
        self.assertEqual(payload["to"], ["alfred@example.com"])
        self.assertEqual(payload["cc"], ["neon@example.com"])
        self.assertEqual(payload["subject"], "Cruisery flyers")
        self.assertTrue(payload["text"].endswith("\n\n- Neon V2"))

    def test_build_send_payload_does_not_duplicate_signature(self):
        payload = build_send_payload(
            to=["alfred@example.com"],
            cc=[],
            subject="Cruisery flyers",
            text="Already signed.\n\n- Neon V2",
        )
        self.assertEqual(payload["text"].count("- Neon V2"), 1)

    def test_summarize_send_result_returns_receipt(self):
        result = summarize_send_result(
            http_status=200,
            body={"message_id": "<msg>", "thread_id": "thread-1"},
            payload={"to": ["alfred@example.com"], "cc": [], "subject": "Test", "text": "Body"},
            inbox="neon_blonde@agentmail.to",
        )
        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["message_id"], "<msg>")
        self.assertEqual(result["thread_id"], "thread-1")
        self.assertNotIn("Body", result)

    def test_build_fallback_draft_keeps_body_for_gmail_tool(self):
        payload = build_send_payload(
            to=["alfred@example.com"],
            cc=["neon@example.com"],
            subject="Cruisery flyers",
            text="The flyers are ready.",
        )
        fallback = build_fallback_draft(payload, reason_code="AGENTMAIL_SEND_FAILED")
        self.assertEqual(fallback["status"], "gmail_draft_required")
        self.assertEqual(fallback["reason_code"], "AGENTMAIL_SEND_FAILED")
        self.assertEqual(fallback["draft"]["to"], "alfred@example.com")
        self.assertEqual(fallback["draft"]["cc"], "neon@example.com")
        self.assertIn("The flyers are ready.", fallback["draft"]["body"])


if __name__ == "__main__":
    unittest.main()
