from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from telegram_bot.booking_watcher.agentmail_alerts import AgentMailAlertSender
from telegram_bot.booking_watcher.detector import detect_booking_signal
from telegram_bot.booking_watcher.models import ArchivedTelegramMessage, QueueItem
from telegram_bot.booking_watcher.store import BookingWatcherStore
from telegram_bot.telegram_transport import IncomingTelegramMessage


class AgentMailSender(Protocol):
    def send_flag(self, item: QueueItem) -> dict[str, object]:
        ...


@dataclass(frozen=True)
class WatcherResult:
    queue_item: QueueItem | None
    alert_text: str | None


class BookingWatcherService:
    def __init__(self, root: Path, *, agentmail_sender: AgentMailSender | None = None) -> None:
        self.store = BookingWatcherStore(root)
        self._agentmail_sender = agentmail_sender or AgentMailAlertSender()

    def handle_text_message(
        self,
        *,
        chat_id: int,
        message_id: int,
        sender_name: str,
        sender_username: str | None,
        text: str,
        message_date: int | None,
    ) -> WatcherResult:
        message = ArchivedTelegramMessage(
            chat_id=chat_id,
            message_id=message_id,
            sender_name=sender_name,
            sender_username=sender_username,
            text=text,
            message_date=message_date,
        )
        self.store.archive_message(message)
        signal = detect_booking_signal(text)
        if signal is None:
            return WatcherResult(queue_item=None, alert_text=None)

        item = self.store.add_queue_item(
            message,
            signal,
            calendar_match="unknown",
            bandsheet_match="unknown",
        )
        if signal.priority != "high":
            return WatcherResult(queue_item=item, alert_text=None)

        self.store.mark_alerted(item.id)
        alerted_item = self.store.get_item(item.id) or item
        self._agentmail_sender.send_flag(alerted_item)
        return WatcherResult(queue_item=alerted_item, alert_text=_build_alert_text(alerted_item))

    def handle_incoming_message(self, message: IncomingTelegramMessage) -> list[str]:
        result = self.handle_text_message(
            chat_id=message.chat_id,
            message_id=message.message_id,
            sender_name=message.sender_name,
            sender_username=message.sender_username,
            text=message.text,
            message_date=message.date,
        )
        return [result.alert_text] if result.alert_text else []


def _build_alert_text(item: QueueItem) -> str:
    signal_label = item.signal_type.replace("_", " ")
    date_line = item.extracted_date or "date unclear"
    return "\n".join(
        [
            "NEON CALENDAR FLAG",
            "",
            f"{item.source_sender_name} mentioned a possible {signal_label}:",
            f'"{item.message_text}"',
            "",
            f"Date: {date_line}",
            "Mike needs to verify/update the calendar if this affects a booking.",
            "Reply here if this is wrong.",
        ]
    )
