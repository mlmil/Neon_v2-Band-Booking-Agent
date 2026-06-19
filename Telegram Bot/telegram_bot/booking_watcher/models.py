from dataclasses import dataclass


@dataclass(frozen=True)
class ArchivedTelegramMessage:
    chat_id: int
    message_id: int
    sender_name: str
    sender_username: str | None
    text: str
    message_date: int | None


@dataclass(frozen=True)
class BookingSignal:
    signal_type: str
    priority: str
    confidence: float
    extracted_date: str | None
    extracted_venue: str | None
    reason: str


@dataclass(frozen=True)
class QueueItem:
    id: str
    created_at: str
    source_chat_id: int
    source_message_id: int
    source_sender_name: str
    source_sender_username: str | None
    message_date: int | None
    message_text: str
    signal_type: str
    extracted_date: str | None
    extracted_venue: str | None
    confidence: float
    calendar_match: str
    bandsheet_match: str
    priority: str
    status: str
    alerted_at: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None
