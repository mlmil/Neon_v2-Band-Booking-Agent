import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from telegram_bot.booking_watcher.models import QueueItem


DEFAULT_AGENTMAIL_INBOX = "neon_blonde@agentmail.to"
DEFAULT_AGENTMAIL_TO = ["neonblondevc@gmail.com", "sin.chonies.inc@gmail.com"]
AGENTMAIL_BASE_URL = "https://api.agentmail.to"

AgentMailRequest = Callable[[str, dict[str, object]], tuple[int, dict[str, object]]]


@dataclass(frozen=True)
class AgentMailFlagMessage:
    to: list[str]
    subject: str
    text: str


class AgentMailAlertSender:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        inbox: str = DEFAULT_AGENTMAIL_INBOX,
        to: list[str] | None = None,
        request: AgentMailRequest | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("AGENTMAIL_API_KEY")
        self._inbox = inbox
        self._to = to or DEFAULT_AGENTMAIL_TO
        self._request = request or self._agentmail_request

    def send_flag(self, item: QueueItem) -> dict[str, object]:
        if not self._api_key:
            return {"status": "blocked", "code": "AGENTMAIL_API_KEY_MISSING", "queue_id": item.id}
        message = build_agentmail_flag_message(item, to=self._to)
        endpoint = f"/v0/inboxes/{self._inbox}/messages/send"
        status, body = self._request(
            endpoint,
            {
                "to": message.to,
                "subject": message.subject,
                "text": message.text,
            },
        )
        if status != 200:
            return {
                "status": "blocked",
                "code": "AGENTMAIL_SEND_FAILED",
                "http_status": status,
                "queue_id": item.id,
            }
        return {
            "status": "sent",
            "queue_id": item.id,
            "message_id": body.get("message_id"),
            "thread_id": body.get("thread_id"),
        }

    def _agentmail_request(self, endpoint: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{AGENTMAIL_BASE_URL}{endpoint}",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                text = response.read().decode("utf-8")
                return response.status, json.loads(text) if text else {}
        except HTTPError as exc:
            return exc.code, {}
        except (OSError, URLError, TimeoutError):
            return 0, {}


def build_agentmail_flag_message(item: QueueItem, *, to: list[str] | None = None) -> AgentMailFlagMessage:
    signal_label = item.signal_type.replace("_", " ")
    date_label = item.extracted_date or "date unclear"
    subject = f"NEON CALENDAR FLAG: possible {signal_label} - {date_label}"
    body = "\n".join(
        [
            "NEON CALENDAR FLAG",
            "",
            f"Source: {item.source_sender_name} in Telegram",
            f'Message: "{item.message_text}"',
            f"Signal: {item.signal_type}",
            f"Date: {date_label}",
            f"Calendar status: {item.calendar_match}",
            f"Band Sheet status: {item.bandsheet_match}",
            f"Queue ID: {item.id}",
            "",
            "Mike action:",
            "Review Google Calendar manually.",
            "No Calendar changes were made by the bot.",
            "",
            "- Neon V2",
        ]
    )
    return AgentMailFlagMessage(to=to or DEFAULT_AGENTMAIL_TO, subject=subject, text=body)
