#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from scripts.intake_email_parser import MONTHS, parse_booking_request


CALENDAR_ICS_URL = "https://calendar.google.com/calendar/ical/neonblondevc%40gmail.com/public/basic.ics"
DEFAULT_CHAT_ID = 7118814432
DEFAULT_ACTIVE_EMAIL_PATH = Path.home() / ".hermes" / "neon_active_booking_email.json"


def _sender_parts(sender: str) -> tuple[str, str]:
    match = re.match(r'\s*"?([^"<]*)"?\s*<([^>]+)>', sender)
    if match:
        return match.group(1).strip() or match.group(2).strip(), match.group(2).strip()
    return sender.strip(), sender.strip()


def _human_date(body: str) -> str | None:
    match = re.search(
        r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*\d{4})?\b",
        body,
        re.IGNORECASE,
    )
    return f"{match.group(1).title()} {int(match.group(2))}" if match else None


def _calendar_has_date(calendar_text: str, iso_date: str) -> bool:
    compact = iso_date.replace("-", "")
    return bool(re.search(rf"DTSTART(?:;[^:]*)?:{compact}(?:T|\b)", calendar_text))


def fetch_public_calendar() -> str:
    with urlopen(CALENDAR_ICS_URL, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def check_date_availability(iso_date: str | None, *, fetch_calendar=fetch_public_calendar) -> str:
    if not iso_date:
        return "uncertain"
    results = []
    for _ in range(2):
        try:
            results.append("conflict" if _calendar_has_date(fetch_calendar(), iso_date) else "clear")
        except Exception:
            results.append("uncertain")
    return results[0] if results[0] == results[1] else "uncertain"


def summarize_email(item: dict, availability: str) -> str:
    sender_name, _ = _sender_parts(str(item.get("sender", "Unknown")))
    body = re.sub(r"\s+", " ", str(item.get("body", ""))).strip()
    preview = body[:900] + ("…" if len(body) > 900 else "")
    count = int(item.get("thread_message_count") or len(item.get("thread_messages") or []))
    availability_line = "" if availability == "uncertain" else f"\nCalendar check: {availability}."
    return (
        f"📧 EMAIL ACTION — {sender_name}\n"
        f"Subject: {item.get('subject', '(no subject)')}\n"
        f"Conversation history: {count or 1} message(s).{availability_line}\n\n"
        f"Latest message:\n{preview or '(no readable body)'}\n\n"
        "Neon V2 has preserved the conversation context. Reply here if you want the assistant to prepare the approval draft."
    )


class BookingEmailNotifier:
    def __init__(
        self,
        *,
        telegram_token: str,
        chat_id: int = DEFAULT_CHAT_ID,
        active_email_path: Path = DEFAULT_ACTIVE_EMAIL_PATH,
        telegram_request=None,
        calendar_fetch=fetch_public_calendar,
        summarizer=summarize_email,
    ) -> None:
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.active_email_path = active_email_path
        self.telegram_request = telegram_request or self._telegram_request
        self.calendar_fetch = calendar_fetch
        self.summarizer = summarizer

    @classmethod
    def from_defaults(cls) -> "BookingEmailNotifier":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        chat_id = int(os.environ.get("NEON_EMAIL_TRIAGE_CHAT_ID", DEFAULT_CHAT_ID))
        return cls(telegram_token=token, chat_id=chat_id)

    def notify(self, item: dict) -> dict:
        parsed = parse_booking_request(str(item.get("body", "")))
        availability = check_date_availability(parsed.get("date"), fetch_calendar=self.calendar_fetch)
        text = self.summarizer(item, availability)
        if len(text) > 4000:
            text = text[:4000] + "\n...[truncated]"
        response = self.telegram_request("sendMessage", {"chat_id": self.chat_id, "text": text})
        if response.get("ok") is not True:
            return {"status": "failed", "availability": availability}

        sender_name, sender_email = _sender_parts(str(item.get("sender", "Unknown")))
        active = {
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": str(item.get("subject", "")),
            "date": str(item.get("date", "")),
            "message_id": str(item.get("message_id", "")),
            "body": str(item.get("body", "")),
            "availability": availability,
            "gmail_thread_id": str(item.get("gmail_thread_id", "")),
            "thread_messages": item.get("thread_messages") or [],
            "thread_message_count": int(item.get("thread_message_count") or 0),
        }
        self.active_email_path.parent.mkdir(parents=True, exist_ok=True)
        self.active_email_path.write_text(json.dumps(active, indent=2), encoding="utf-8")
        return {"status": "sent", "availability": availability}

    def _telegram_request(self, method: str, payload: dict) -> dict:
        request = Request(
            f"https://api.telegram.org/bot{self.telegram_token}/{method}",
            data=urlencode(payload).encode("utf-8"),
            method="POST",
        )
        with urlopen(request, timeout=20) as response:
            result = json.load(response)
        return result if isinstance(result, dict) else {"ok": False}
