import unittest

from telegram_bot.booking_watcher.agentmail_alerts import AgentMailAlertSender, build_agentmail_flag_message
from telegram_bot.booking_watcher.models import QueueItem


class AgentMailAlertTests(unittest.TestCase):
    def test_builds_internal_flag_message_for_mike_and_alfred(self) -> None:
        item = _queue_item()

        message = build_agentmail_flag_message(item)

        self.assertEqual(message.subject, "NEON CALENDAR FLAG: possible cancellation - June 27")
        self.assertEqual(message.to, ["neonblondevc@gmail.com", "sin.chonies.inc@gmail.com"])
        self.assertIn("Source: Kyle in Telegram", message.text)
        self.assertIn('Message: "June 27 is canceled"', message.text)
        self.assertIn("No Calendar changes were made by the bot.", message.text)

    def test_sender_posts_to_agentmail_send_endpoint(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(endpoint: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
            calls.append((endpoint, payload))
            return 200, {"message_id": "msg-1", "thread_id": "thread-1"}

        sender = AgentMailAlertSender(api_key="test-key", request=request)

        result = sender.send_flag(_queue_item())

        self.assertEqual(result["status"], "sent")
        self.assertEqual(calls[0][0], "/v0/inboxes/neon_blonde@agentmail.to/messages/send")
        self.assertEqual(calls[0][1]["to"], ["neonblondevc@gmail.com", "sin.chonies.inc@gmail.com"])

    def test_missing_api_key_blocks_without_exception(self) -> None:
        sender = AgentMailAlertSender(api_key="", request=lambda endpoint, payload: (200, {}))

        result = sender.send_flag(_queue_item())

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "AGENTMAIL_API_KEY_MISSING")


def _queue_item() -> QueueItem:
    return QueueItem(
        id="flag-m1001-42",
        created_at="2026-06-16T12:00:00+00:00",
        source_chat_id=-1001,
        source_message_id=42,
        source_sender_name="Kyle",
        source_sender_username="kyle",
        message_date=1719000000,
        message_text="June 27 is canceled",
        signal_type="cancellation",
        extracted_date="June 27",
        extracted_venue=None,
        confidence=0.75,
        calendar_match="unknown",
        bandsheet_match="unknown",
        priority="high",
        status="alerted",
    )


if __name__ == "__main__":
    unittest.main()
