import json
import tempfile
import unittest
from pathlib import Path

from scripts.booking_email_notifier import (
    BookingEmailNotifier,
    check_date_availability,
)


BOOKING_EMAIL = {
    "sender": "Mike Test <mike@sparkai805.com>",
    "subject": "Party booking in Pismo Beach",
    "date": "Thu, 18 Jun 2026 09:00:00 -0700",
    "message_id": "<spark-test-1>",
    "body": (
        "Hi, my name is Mike. We are having a party in Pismo Beach on July 10 "
        "at 7pm. Are you available and how much do you charge?"
    ),
}


class BookingEmailNotifierTests(unittest.TestCase):
    def test_two_matching_calendar_checks_can_mark_date_clear(self):
        calls = []

        def fetch_calendar():
            calls.append(True)
            return "BEGIN:VCALENDAR\nEND:VCALENDAR"

        result = check_date_availability("2026-07-10", fetch_calendar=fetch_calendar)

        self.assertEqual(result, "clear")
        self.assertEqual(len(calls), 2)

    def test_calendar_conflict_blocks_clear_result(self):
        calendar = "\n".join(
            [
                "BEGIN:VCALENDAR",
                "BEGIN:VEVENT",
                "DTSTART:20260710T190000",
                "SUMMARY:Existing Gig",
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        result = check_date_availability("2026-07-10", fetch_calendar=lambda: calendar)

        self.assertEqual(result, "conflict")

    def test_disagreeing_calendar_checks_are_uncertain(self):
        calendars = iter(
            [
                "BEGIN:VCALENDAR\nEND:VCALENDAR",
                "BEGIN:VCALENDAR\nDTSTART:20260710T190000\nSUMMARY:Existing Gig\nEND:VCALENDAR",
            ]
        )

        result = check_date_availability("2026-07-10", fetch_calendar=lambda: next(calendars))

        self.assertEqual(result, "uncertain")

    def test_notify_sends_telegram_and_persists_active_email(self):
        calls = []

        def telegram_request(method, payload):
            calls.append((method, payload))
            return {"ok": True}

        with tempfile.TemporaryDirectory() as tmp:
            active_path = Path(tmp) / "active.json"
            notifier = BookingEmailNotifier(
                telegram_token="test-token",
                chat_id=7118814432,
                active_email_path=active_path,
                telegram_request=telegram_request,
                calendar_fetch=lambda: "BEGIN:VCALENDAR\nEND:VCALENDAR",
                summarizer=lambda item, availability: "Mike replied that Friday works. Want me to draft the next response?",
            )

            result = notifier.notify(BOOKING_EMAIL)

            self.assertEqual(result["status"], "sent")
            self.assertEqual(calls[0][0], "sendMessage")
            self.assertEqual(calls[0][1]["chat_id"], 7118814432)
            self.assertIn("Mike replied", calls[0][1]["text"])
            saved = json.loads(active_path.read_text())
            self.assertEqual(saved["message_id"], "<spark-test-1>")
            self.assertEqual(saved["sender_email"], "mike@sparkai805.com")

    def test_failed_telegram_send_does_not_replace_active_email(self):
        with tempfile.TemporaryDirectory() as tmp:
            active_path = Path(tmp) / "active.json"
            active_path.write_text('{"message_id":"older"}')
            notifier = BookingEmailNotifier(
                telegram_token="test-token",
                chat_id=7118814432,
                active_email_path=active_path,
                telegram_request=lambda method, payload: {"ok": False},
                calendar_fetch=lambda: "BEGIN:VCALENDAR\nEND:VCALENDAR",
                summarizer=lambda item, availability: "Summary",
            )

            result = notifier.notify(BOOKING_EMAIL)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(json.loads(active_path.read_text())["message_id"], "older")


if __name__ == "__main__":
    unittest.main()
