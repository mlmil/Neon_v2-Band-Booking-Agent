import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.booking_watcher.models import ArchivedTelegramMessage, BookingSignal
from telegram_bot.booking_watcher.store import BookingWatcherStore


class BookingWatcherStoreTests(unittest.TestCase):
    def test_archives_message_and_adds_queue_item(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = BookingWatcherStore(Path(temp_dir))
            message = ArchivedTelegramMessage(
                chat_id=-1001,
                message_id=42,
                sender_name="Kyle",
                sender_username="kyle",
                text="June 27 is canceled",
                message_date=1719000000,
            )
            signal = BookingSignal("cancellation", "high", 0.75, "June 27", None, "matched cancellation keyword")

            store.archive_message(message)
            item = store.add_queue_item(message, signal, calendar_match="booked", bandsheet_match="booked")

            self.assertEqual(item.status, "open")
            self.assertEqual(item.signal_type, "cancellation")
            self.assertEqual(len(store.list_open_items()), 1)

    def test_mark_reviewed_updates_queue_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = BookingWatcherStore(Path(temp_dir))
            message = ArchivedTelegramMessage(-1001, 42, "Kyle", "kyle", "June 27 is canceled", 1719000000)
            signal = BookingSignal("cancellation", "high", 0.75, "June 27", None, "matched cancellation keyword")
            item = store.add_queue_item(message, signal, calendar_match="booked", bandsheet_match="unknown")

            self.assertTrue(store.mark_reviewed(item.id, reviewed_by="Mike"))

            open_items = store.list_open_items()
            self.assertEqual(open_items, [])
            reviewed = store.get_item(item.id)
            assert reviewed is not None
            self.assertEqual(reviewed.status, "reviewed")
            self.assertEqual(reviewed.reviewed_by, "Mike")


if __name__ == "__main__":
    unittest.main()
