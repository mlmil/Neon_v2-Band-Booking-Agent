import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.booking_watcher.service import BookingWatcherService


class BookingWatcherServiceTests(unittest.TestCase):
    def test_high_priority_message_creates_alert_and_queue_item(self) -> None:
        with TemporaryDirectory() as temp_dir:
            agentmail = FakeAgentMailSender()
            service = BookingWatcherService(Path(temp_dir), agentmail_sender=agentmail)

            result = service.handle_text_message(
                chat_id=-1001,
                message_id=42,
                sender_name="Kyle",
                sender_username="kyle",
                text="June 27 is canceled",
                message_date=1719000000,
            )

            self.assertIsNotNone(result.alert_text)
            assert result.alert_text is not None
            self.assertIn("NEON CALENDAR FLAG", result.alert_text)
            self.assertIn("possible cancellation", result.alert_text)
            self.assertEqual(len(service.store.list_open_items()), 1)
            self.assertEqual(agentmail.sent_ids, ["flag-m1001-42"])

    def test_ordinary_message_archives_without_alert(self) -> None:
        with TemporaryDirectory() as temp_dir:
            agentmail = FakeAgentMailSender()
            service = BookingWatcherService(Path(temp_dir), agentmail_sender=agentmail)

            result = service.handle_text_message(
                chat_id=-1001,
                message_id=43,
                sender_name="Dave",
                sender_username=None,
                text="Great rehearsal.",
                message_date=1719000001,
            )

            self.assertIsNone(result.alert_text)
            self.assertEqual(service.store.list_open_items(), [])
            self.assertEqual(agentmail.sent_ids, [])


class FakeAgentMailSender:
    def __init__(self) -> None:
        self.sent_ids: list[str] = []

    def send_flag(self, item) -> dict[str, object]:
        self.sent_ids.append(item.id)
        return {"status": "sent", "queue_id": item.id}


if __name__ == "__main__":
    unittest.main()
