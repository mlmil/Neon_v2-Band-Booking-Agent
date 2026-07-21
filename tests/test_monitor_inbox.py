import tempfile
import unittest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.monitor_inbox import (
    build_flagged_email,
    create_intake_receipts_for_flagged,
    fetch_flagged_messages_imap,
    fetch_gmail_thread,
    process_flagged_messages,
    redact_secrets,
    get_body_from_message,
)

class MonitorInboxIMAPTests(unittest.TestCase):
    def test_fetch_gmail_thread_preserves_more_than_forty_messages(self):
        import email.message

        payloads = {}
        for index in range(45):
            message = email.message.EmailMessage()
            message["From"] = (
                "Neon Blonde <neonblondevc@gmail.com>"
                if index % 2
                else "Jeff <jeff@example.com>"
            )
            message["To"] = "Jeff <jeff@example.com>"
            message["Subject"] = "Wedding details"
            message["Date"] = (
                datetime(2026, 6, 1, 10, tzinfo=timezone(timedelta(hours=-7)))
                + timedelta(days=index)
            ).strftime("%a, %d %b %Y %H:%M:%S %z")
            message["Message-ID"] = f"<message-{index}>"
            message.set_content(f"Thread message {index}")
            payloads[str(index + 1).encode()] = message.as_bytes()

        class FakeMail:
            def select(self, *_args, **_kwargs):
                return "OK", []

            def search(self, *_args):
                return "OK", [b" ".join(payloads)]

            def fetch(self, mid, _query):
                return "OK", [(b"RFC822", payloads[mid])]

        messages = fetch_gmail_thread(
            FakeMail(),
            thread_id="12345",
            account_email="neonblondevc@gmail.com",
        )

        self.assertEqual(len(messages), 45)
        self.assertEqual(messages[0]["direction"], "received")
        self.assertEqual(messages[1]["direction"], "sent")
        self.assertIn("Thread message 44", messages[-1]["text"])

    def test_build_flagged_email_detects_booking_keyword(self):
        flagged = build_flagged_email(
            sender="Phillip <phillip@example.com>",
            subject="M Special August date",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Can we book M Special on August 15 at 7pm in Goleta?",
            message_id="<msg-1>",
        )

        self.assertIsNotNone(flagged)
        self.assertFalse(flagged["vip"])
        self.assertEqual(flagged["message_id"], "<msg-1>")
        self.assertIn("Can we book", flagged["body"])

    def test_build_flagged_email_ignores_non_actionable_message(self):
        flagged = build_flagged_email(
            sender="Newsletter <news@example.com>",
            subject="Weekly specials",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Here are this week's food specials.",
        )
        self.assertIsNone(flagged)

    def test_build_flagged_email_detects_party_performance_request(self):
        flagged = build_flagged_email(
            sender="Mike Miller <mike@sparkai805.com>",
            subject="Neon blonde play my birthday party? (test)",
            date_str="Thu, 18 Jun 2026 00:44:19 -0700",
            body=(
                "I live in Pismo Beach and I'm having a birthday party on October 10th. "
                "Could you possibly play that party, and how much do you charge?"
            ),
            message_id="<spark-party-test>",
        )

        self.assertIsNotNone(flagged)

    def test_create_intake_receipts_for_flagged_writes_local_receipt(self):
        flagged = build_flagged_email(
            sender="Phillip <phillip@example.com>",
            subject="M Special August date",
            date_str="Tue, 09 Jun 2026 10:00:00 -0700",
            body="Can we book M Special on August 15 at 7pm in Goleta?",
            message_id="<msg-1>",
        )

        with tempfile.TemporaryDirectory() as tmp:
            paths = create_intake_receipts_for_flagged([flagged], Path(tmp))

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].exists())
            self.assertIn("m-special", paths[0].name)

            # Check raw body is absent
            with open(paths[0], 'r') as f:
                content = json.load(f)
                self.assertNotIn("email_text", content)
                self.assertNotIn("body", content)

    def test_redact_secrets(self):
        body = "Here is my password: secret_123! and my API key: AKIAIOSFODNN7EXAMPLE. Bearer xyz123"
        redacted = redact_secrets(body)
        self.assertNotIn("secret_123", redacted)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", redacted)
        self.assertNotIn("xyz123", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_get_body_extracts_plain_text(self):
        import email.message
        msg = email.message.EmailMessage()
        msg.set_payload("Hello world")
        msg.set_type("text/plain")
        body = get_body_from_message(msg)
        self.assertEqual(body.strip(), "Hello world")

    def test_process_flagged_notifies_then_marks_processed(self):
        item = build_flagged_email(
            sender="Mike <mike@sparkai805.com>",
            subject="Party booking",
            date_str="Thu, 18 Jun 2026 09:00:00 -0700",
            body="Can Neon Blonde play our party in Pismo Beach on July 10 at 7pm? How much do you charge?",
            message_id="<spark-1>",
        )
        notified = []

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "processed.json"
            paths = process_flagged_messages(
                [item],
                receipt_dir=Path(tmp) / "receipts",
                state_path=state,
                notifier=lambda value: notified.append(value) or {"status": "sent"},
            )

            self.assertEqual(len(paths), 1)
            self.assertEqual(len(notified), 1)
            self.assertIn("<spark-1>", json.loads(state.read_text())["processed_ids"])

    def test_process_flagged_does_not_mark_processed_when_notification_fails(self):
        item = build_flagged_email(
            sender="Mike <mike@sparkai805.com>",
            subject="Party booking",
            date_str="Thu, 18 Jun 2026 09:00:00 -0700",
            body="Can Neon Blonde play our party in Pismo Beach on July 10 at 7pm?",
            message_id="<spark-2>",
        )

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "processed.json"
            with self.assertRaises(RuntimeError):
                process_flagged_messages(
                    [item],
                    receipt_dir=Path(tmp) / "receipts",
                    state_path=state,
                    notifier=lambda value: {"status": "failed"},
                )

            self.assertFalse(state.exists())

    @patch("scripts.monitor_inbox.imaplib.IMAP4_SSL")
    def test_fetch_flagged_messages_imap_skips_processed(self, mock_imap_cls):
        mock_mail = MagicMock()
        mock_imap_cls.return_value = mock_mail

        # Mock search to return 2 messages
        mock_mail.search.return_value = ('OK', [b'1 2'])

        # We process message "1" (which has <msg-1>) and message "2" (which has <msg-2>)
        # Message 1 is in processed_ids, so it should be skipped. Wait, UID vs Message-ID:
        # In IMAP we fetch the header to check Message-ID first.

        mock_mail.fetch.side_effect = [
            ('OK', [b'1 (UID 101)']),
            ('OK', [b'2 (UID 202)']),
            ('OK', [(b'2 (RFC822)', b'Message-ID: <msg-2>\r\nSubject: New Gig\r\nFrom: vip@rockstarentertainment.com\r\nDate: 2026-06-10\r\nContent-Type: text/plain\r\n\r\nBook us for a gig')])
        ]

        processed_ids = {"imap:neonblondevc@gmail.com:101"}

        count, flagged = fetch_flagged_messages_imap(
            config={"email": "neonblondevc@gmail.com", "app_password": "app-pass"},
            processed_ids=processed_ids,
            max_results=10,
        )

        self.assertEqual(count, 1) # only 1 new message fetched fully
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["message_id"], "imap:neonblondevc@gmail.com:202")

        # Ensure store() is never called
        self.assertFalse(mock_mail.store.called)

if __name__ == "__main__":
    unittest.main()
