import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from telegram_bot.booking_watcher.models import ArchivedTelegramMessage, BookingSignal, QueueItem


class BookingWatcherStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.archive_path = root / "archive.jsonl"
        self.queue_path = root / "queue.jsonl"

    def archive_message(self, message: ArchivedTelegramMessage) -> None:
        self._append_jsonl(self.archive_path, asdict(message))

    def add_queue_item(
        self,
        message: ArchivedTelegramMessage,
        signal: BookingSignal,
        *,
        calendar_match: str,
        bandsheet_match: str,
    ) -> QueueItem:
        item = QueueItem(
            id=self._build_id(message),
            created_at=_now_iso(),
            source_chat_id=message.chat_id,
            source_message_id=message.message_id,
            source_sender_name=message.sender_name,
            source_sender_username=message.sender_username,
            message_date=message.message_date,
            message_text=message.text,
            signal_type=signal.signal_type,
            extracted_date=signal.extracted_date,
            extracted_venue=signal.extracted_venue,
            confidence=signal.confidence,
            calendar_match=calendar_match,
            bandsheet_match=bandsheet_match,
            priority=signal.priority,
            status="open",
        )
        items = [existing for existing in self._read_queue_items() if existing.id != item.id]
        items.append(item)
        self._write_queue_items(items)
        return item

    def list_open_items(self) -> list[QueueItem]:
        return [item for item in self._read_queue_items() if item.status in {"open", "alerted"}]

    def get_item(self, item_id: str) -> QueueItem | None:
        for item in self._read_queue_items():
            if item.id == item_id:
                return item
        return None

    def mark_reviewed(self, item_id: str, *, reviewed_by: str) -> bool:
        return self._update_status(item_id, status="reviewed", reviewed_by=reviewed_by)

    def mark_dismissed(self, item_id: str, *, reviewed_by: str) -> bool:
        return self._update_status(item_id, status="dismissed", reviewed_by=reviewed_by)

    def mark_alerted(self, item_id: str) -> bool:
        items = self._read_queue_items()
        changed = False
        updated: list[QueueItem] = []
        for item in items:
            if item.id == item_id:
                item = QueueItem(**{**asdict(item), "status": "alerted", "alerted_at": _now_iso()})
                changed = True
            updated.append(item)
        if changed:
            self._write_queue_items(updated)
        return changed

    def _update_status(self, item_id: str, *, status: str, reviewed_by: str) -> bool:
        items = self._read_queue_items()
        changed = False
        updated: list[QueueItem] = []
        for item in items:
            if item.id == item_id:
                item = QueueItem(
                    **{
                        **asdict(item),
                        "status": status,
                        "reviewed_at": _now_iso(),
                        "reviewed_by": reviewed_by,
                    }
                )
                changed = True
            updated.append(item)
        if changed:
            self._write_queue_items(updated)
        return changed

    def _read_queue_items(self) -> list[QueueItem]:
        if not self.queue_path.exists():
            return []
        items: list[QueueItem] = []
        for line in self.queue_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(QueueItem(**json.loads(line)))
        return items

    def _write_queue_items(self, items: list[QueueItem]) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(json.dumps(asdict(item), sort_keys=True) + "\n" for item in items)
        self.queue_path.write_text(payload, encoding="utf-8")

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _build_id(self, message: ArchivedTelegramMessage) -> str:
        chat = str(message.chat_id).replace("-", "m")
        return f"flag-{chat}-{message.message_id}"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
