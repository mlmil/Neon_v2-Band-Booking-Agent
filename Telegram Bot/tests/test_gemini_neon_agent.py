import json
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.gemini_agent import GeminiNeonAgent
from telegram_bot.providers.email_context import EmailMessage, NeonEmailProvider


class FakeEmailProvider:
    def latest_actionable(self) -> EmailMessage:
        return EmailMessage(
            sender_name="Phillip Thomas",
            sender_email="rockstarentertainment805@gmail.com",
            subject="New confirmed date",
            date="Wed, 17 Jun 2026 22:45:39 -0700",
            message_id="<message-id>",
            body=(
                "new confirmed date:\nFIG MOUNTAIN BREWERY (funk Zone)\n"
                "Friday, September 11th\n7:00 to 10:00\n$500"
            ),
        )


class FakeCalendar:
    def describe_date(self, date_text: str) -> str:
        return "September 11, 2026 is not on the Neon calendar."


class OnCalendar:
    def describe_date(self, date_text: str) -> str:
        return "September 11, 2026 is on the Neon calendar."


class FakeModel:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def respond(self, prompt: str) -> dict[str, object]:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class FakeSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    def send(self, *, to: list[str], subject: str, text: str) -> dict[str, object]:
        self.sent.append({"to": to, "subject": subject, "text": text})
        return {"status": "sent", "message_id": "msg-1"}


class GeminiNeonAgentTests(unittest.TestCase):
    def test_email_provider_prefers_persisted_active_booking_email(self) -> None:
        with TemporaryDirectory() as temp_dir:
            active_path = Path(temp_dir) / "active.json"
            active_path.write_text(
                json.dumps(
                    {
                        "sender_name": "Mike Test",
                        "sender_email": "mike@sparkai805.com",
                        "subject": "Pismo party",
                        "date": "Thu, 18 Jun 2026 09:00:00 -0700",
                        "message_id": "<spark-test>",
                        "body": "Can you play July 10? How much do you charge?",
                    }
                )
            )

            message = NeonEmailProvider(
                config_path=Path(temp_dir) / "missing-config.json",
                active_email_path=active_path,
            ).latest_actionable()

        self.assertEqual(message.sender_name, "Mike Test")
        self.assertEqual(message.sender_email, "mike@sparkai805.com")
        self.assertEqual(message.message_id, "<spark-test>")

    def test_gemini_can_explain_email_and_offer_draft_naturally(self) -> None:
        model = FakeModel(
            [
                {
                    "reply": (
                        "Phillip confirmed Fig Mountain for September 11, 7-10 PM at $500. "
                        "It is not on the calendar yet. Want me to draft a reply?"
                    ),
                    "draft": None,
                    "send_current_draft": False,
                }
            ]
        )
        with TemporaryDirectory() as temp_dir:
            agent = GeminiNeonAgent(
                state_path=Path(temp_dir) / "state.json",
                model=model,
                email_provider=FakeEmailProvider(),
                calendar=FakeCalendar(),
                sender=FakeSender(),
            )

            reply = agent.reply("What does Phillip want?")

        self.assertIn("September 11", reply)
        self.assertIn("not on the calendar", reply)
        self.assertIn("actual incoming email", model.prompts[0])

    def test_draft_is_saved_and_displayed_but_not_sent(self) -> None:
        model = FakeModel(
            [
                {
                    "reply": "Here is a draft. Tell me what you want changed, or approve it when ready.",
                    "draft": {
                        "to": ["rockstarentertainment805@gmail.com"],
                        "subject": "Re: New confirmed date",
                        "body": "Hi Phillip,\n\nThanks. I have September 11 at 7-10 PM for $500.\n\n- Neon V2",
                    },
                    "send_current_draft": False,
                }
            ]
        )
        sender = FakeSender()
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            agent = GeminiNeonAgent(
                state_path=state_path,
                model=model,
                email_provider=FakeEmailProvider(),
                calendar=OnCalendar(),
                sender=sender,
                allow_send=True,
            )

            reply = agent.reply("Draft something that confirms the details.")

            self.assertIn("Hi Phillip", reply)
            self.assertEqual(sender.sent, [])
            self.assertTrue(state_path.exists())

    def test_natural_approval_sends_only_previously_displayed_current_draft(self) -> None:
        model = FakeModel(
            [
                {
                    "reply": "Sending the draft you approved.",
                    "draft": None,
                    "send_current_draft": True,
                }
            ]
        )
        sender = FakeSender()
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(
                '{"draft":{"to":["rockstarentertainment805@gmail.com"],'
                '"subject":"Re: New confirmed date","body":"Hi Phillip","version":1,'
                '"displayed":true},"history":[]}',
                encoding="utf-8",
            )
            agent = GeminiNeonAgent(
                state_path=state_path,
                model=model,
                email_provider=FakeEmailProvider(),
                calendar=FakeCalendar(),
                sender=sender,
                allow_send=True,
            )

            reply = agent.reply("Looks good, go ahead.")

        self.assertIn("Sent", reply)
        self.assertEqual(len(sender.sent), 1)

    def test_confirmation_send_is_blocked_when_date_is_not_on_calendar(self) -> None:
        model = FakeModel(
            [
                {
                    "reply": "Sending the approved confirmation.",
                    "draft": None,
                    "send_current_draft": True,
                }
            ]
        )
        sender = FakeSender()
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(
                '{"draft":{"to":["rockstarentertainment805@gmail.com"],'
                '"subject":"Re: New confirmed date","body":"September 11 is confirmed.","version":1,'
                '"displayed":true},"history":[]}',
                encoding="utf-8",
            )
            agent = GeminiNeonAgent(
                state_path=state_path,
                model=model,
                email_provider=FakeEmailProvider(),
                calendar=FakeCalendar(),
                sender=sender,
                allow_send=True,
            )

            reply = agent.reply("Looks good, send it.")

        self.assertIn("not on the Neon calendar", reply)
        self.assertEqual(sender.sent, [])

    def test_due_reminder_returns_pending_draft_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "draft": {
                            "to": ["rockstarentertainment805@gmail.com"],
                            "subject": "Re: New confirmed date",
                            "body": "Hi Phillip",
                            "version": 1,
                            "displayed": True,
                        },
                        "remind_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
                        "history": [],
                    }
                ),
                encoding="utf-8",
            )
            agent = GeminiNeonAgent(
                state_path=state_path,
                model=FakeModel([]),
                email_provider=FakeEmailProvider(),
                calendar=FakeCalendar(),
                sender=FakeSender(),
            )

            reminder = agent.due_reminder()

        self.assertIn("Phillip", reminder)
        self.assertIn("Re: New confirmed date", reminder)


if __name__ == "__main__":
    unittest.main()
