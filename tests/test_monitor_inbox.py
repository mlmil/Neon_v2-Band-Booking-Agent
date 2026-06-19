import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.monitor_inbox import (
    build_flagged_email,
    create_intake_receipts_for_flagged,
    fetch_flagged_messages_agentmail,
    fetch_flagged_messages_imap,
    process_flagged_messages,
    redact_secrets,
    get_body
)

class MonitorInboxIMAPTests(unittest.TestCase):
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
        body = get_body(msg)
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

    def test_fetch_flagged_messages_agentmail_reads_human_message_without_booking_keywords(self):
        calls = []

        def request(endpoint):
            calls.append(endpoint)
            if endpoint.endswith("/messages?limit=10"):
                return 200, {
                    "messages": [
                        {
                            "message_id": "<old>",
                            "from": "Old Contact <old@example.com>",
                            "subject": "Old booking",
                            "timestamp": "2026-06-18T07:40:00.000Z",
                            "preview": "Old booking request",
                        },
                        {
                            "message_id": "<new>",
                            "from": "Mike <mike@sparkai805.com>",
                            "subject": "Malibu Party",
                            "timestamp": "2026-06-18T07:58:15.000Z",
                            "thread_id": "thread-new",
                            "labels": ["received", "unread"],
                            "preview": "Sounds good. Friday works for us.",
                        },
                    ]
                }
            if "/threads/" in endpoint:
                return 200, {
                    "thread_id": "thread-new",
                    "messages": [
                        {"from": "Neon <neon_blonde@agentmail.to>", "text": "Would Friday work?"},
                        {"from": "Mike <mike@sparkai805.com>", "text": "Sounds good. Friday works for us."},
                    ],
                }
            return 200, {"text": "Sounds good. Friday works for us."}

        count, flagged = fetch_flagged_messages_agentmail(
            request=request,
            processed_ids={"<old>"},
            max_results=10,
        )

        self.assertEqual(count, 1)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["message_id"], "<new>")
        self.assertEqual(flagged[0]["thread_id"], "thread-new")
        self.assertEqual(len(flagged[0]["thread_messages"]), 2)
        self.assertIn("/v0/inboxes/neon_blonde@agentmail.to/messages?limit=10", calls[0])
        self.assertTrue(any("/threads/thread-new" in endpoint for endpoint in calls[1:]))

    def test_fetch_flagged_messages_agentmail_ignores_forwarding_confirmation(self):
        def request(endpoint):
            return 200, {
                "messages": [
                    {
                        "message_id": "<confirm>",
                        "from": "Gmail Team <forwarding-noreply@google.com>",
                        "subject": "Gmail Forwarding Confirmation",
                        "timestamp": "2026-06-18T07:55:35.000Z",
                        "preview": "Confirm forwarding",
                    }
                ]
            }

        count, flagged = fetch_flagged_messages_agentmail(
            request=request,
            processed_ids=set(),
            max_results=10,
        )

        self.assertEqual(count, 0)
        self.assertEqual(flagged, [])

    @patch("scripts.monitor_inbox.imaplib.IMAP4_SSL")
    def test_fetch_flagged_messages_imap_skips_processed(self, mock_imap_cls):
        mock_mail = MagicMock()
        mock_imap_cls.return_value = mock_mail

        # Mock search to return 2 messages
        mock_mail.search.return_value = ('OK', [b'1 2'])

        # We process message "1" (which has <msg-1>) and message "2" (which has <msg-2>)
        # Message 1 is in processed_ids, so it should be skipped. Wait, UID vs Message-ID:
        # In IMAP we fetch the header to check Message-ID first.

        # Mock fetch to return headers for both
        mock_mail.fetch.side_effect = [
            ('OK', [(b'1 (BODY.PEEK[HEADER])', b'Message-ID: <msg-1>\r\nSubject: Old Gig\r\n\r\n')]),
            # msg-1 skipped, so body is not fetched
            ('OK', [(b'2 (BODY.PEEK[HEADER])', b'Message-ID: <msg-2>\r\nSubject: New Gig\r\nFrom: vip@rockstarentertainment.com\r\nDate: 2026-06-10\r\n\r\n')]),
            # msg-2 is fetched fully
            ('OK', [(b'2 (BODY.PEEK[])', b'Message-ID: <msg-2>\r\nSubject: New Gig\r\nFrom: vip@rockstarentertainment.com\r\nDate: 2026-06-10\r\nContent-Type: text/plain\r\n\r\nBook us for a gig')])
        ]

        processed_ids = {"<msg-1>"}

        count, flagged = fetch_flagged_messages_imap(mock_mail, processed_ids, 10)

        self.assertEqual(count, 1) # only 1 new message fetched fully
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["message_id"], "<msg-2>")

        # Ensure store() is never called
        self.assertFalse(mock_mail.store.called)

        # Ensure only BODY.PEEK is used
        for call in mock_mail.fetch.call_args_list:
            args, _ = call
            self.assertIn(b'PEEK', args[1].encode() if isinstance(args[1], str) else args[1])

if __name__ == "__main__":
    unittest.main()
