import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from telegram_bot.providers.calendar_context import NeonCalendarContext
from telegram_bot.providers.email_context import EmailMessage, NeonEmailProvider
from telegram_bot.providers.gemini import resolve_gemini_command


class GeminiJsonModel:
    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds

    def respond(self, prompt: str) -> dict[str, object]:
        completed = subprocess.run(
            [*resolve_gemini_command(), "--skip-trust", "--approval-mode", "plan", "--prompt", prompt],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError("Gemini agent failed")
        raw = completed.stdout.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < start:
            raise RuntimeError("Gemini agent returned no JSON")
        result = json.loads(raw[start : end + 1])
        if not isinstance(result, dict):
            raise RuntimeError("Gemini agent returned invalid JSON")
        return result


class AgentMailSender:
    def send(self, *, to: list[str], subject: str, text: str) -> dict[str, object]:
        import sys

        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from scripts.agentmail_send import DEFAULT_INBOX, send_agentmail

        return send_agentmail(inbox=DEFAULT_INBOX, to=to, cc=[], subject=subject, text=text)


class GeminiNeonAgent:
    def __init__(
        self,
        *,
        state_path: Path | None = None,
        model=None,
        email_provider=None,
        calendar=None,
        sender=None,
        allow_send: bool = False,
    ) -> None:
        self.state_path = state_path or Path.home() / ".hermes" / "neon_gemini_conversation.json"
        self.model = model or GeminiJsonModel()
        self.email_provider = email_provider or NeonEmailProvider()
        self.calendar = calendar or NeonCalendarContext()
        self.sender = sender or AgentMailSender()
        self.allow_send = allow_send

    def __call__(self, question: str, snapshot=None) -> str:
        return self.reply(question)

    def reply(self, message: str) -> str:
        state = self._load_state()
        email_message = self.email_provider.latest_actionable()
        calendar_status = self._calendar_status(email_message)
        result = self.model.respond(self._prompt(message, state, email_message, calendar_status))

        draft = result.get("draft")
        if isinstance(draft, dict):
            previous_version = state.get("draft", {}).get("version", 0) if isinstance(state.get("draft"), dict) else 0
            state["draft"] = {
                "to": [value for value in draft.get("to", []) if isinstance(value, str)],
                "subject": str(draft.get("subject", "")).strip(),
                "body": str(draft.get("body", "")).strip(),
                "version": previous_version + 1,
                "displayed": True,
            }
            state["remind_at"] = (datetime.now(UTC) + timedelta(hours=2)).isoformat()

        reply = str(result.get("reply", "")).strip() or "I’m here. What do you want to do?"
        if isinstance(draft, dict):
            current = state["draft"]
            reply = "\n".join(
                [
                    reply,
                    "",
                    f"To: {', '.join(current['to'])}",
                    f"Subject: {current['subject']}",
                    "",
                    current["body"],
                    "",
                    "This draft has not been sent.",
                ]
            )

        if result.get("send_current_draft") is True:
            current = state.get("draft")
            if not isinstance(current, dict) or current.get("displayed") is not True:
                reply = "I don’t have a displayed draft to send yet."
            elif not self.allow_send:
                reply = "This is a local preview, so I have not sent the draft."
            elif "confirmed" in current.get("body", "").lower() and "not on the Neon calendar" in calendar_status:
                reply = (
                    f"I have not sent it. {calendar_status} "
                    "Add it to the Calendar first, then tell me it is there and I’ll verify again."
                )
            else:
                send_result = self.sender.send(to=current["to"], subject=current["subject"], text=current["body"])
                if send_result.get("status") == "sent":
                    reply = f"Sent to {', '.join(current['to'])}."
                    state["last_sent"] = {**current, "sent_at": datetime.now(UTC).isoformat()}
                    state.pop("draft", None)
                    state.pop("remind_at", None)
                else:
                    reply = "I could not send the approved draft through AgentMail."

        history = state.setdefault("history", [])
        history.extend([{"role": "mike", "text": message}, {"role": "neon", "text": reply}])
        state["history"] = history[-20:]
        self._save_state(state)
        return reply

    def due_reminder(self) -> str | None:
        state = self._load_state()
        draft = state.get("draft")
        remind_at = state.get("remind_at")
        if not isinstance(draft, dict) or not isinstance(remind_at, str):
            return None
        try:
            due = datetime.fromisoformat(remind_at)
        except ValueError:
            return None
        if due > datetime.now(UTC):
            return None
        state["remind_at"] = (datetime.now(UTC) + timedelta(days=1)).isoformat()
        self._save_state(state)
        recipients = ", ".join(draft.get("to", []))
        contact = "Phillip" if "rockstarentertainment805" in recipients else recipients
        return (
            f"Reminder: the draft to {contact} about “{draft.get('subject', 'pending email')}” "
            "is still waiting for your review. Nothing has been sent."
        )

    def _calendar_status(self, message: EmailMessage | None) -> str:
        if message is None:
            return "No actionable email is currently loaded."
        return self.calendar.describe_date(message.body)

    def _prompt(self, message: str, state: dict, email_message: EmailMessage | None, calendar_status: str) -> str:
        email_context = "No actionable email found."
        if email_message is not None:
            email_context = "\n".join(
                [
                    "This is the actual incoming email:",
                    f"From: {email_message.sender_name} <{email_message.sender_email}>",
                    f"Subject: {email_message.subject}",
                    f"Date: {email_message.date}",
                    email_message.body,
                ]
            )
        return "\n".join(
            [
                "You are Neon V2, a Gemini-powered band operations assistant talking naturally with Mike in Telegram.",
                "Answer conversationally. Do not use canned command-menu language.",
                "You can discuss the actual incoming email, propose drafts, revise drafts, and interpret natural approval.",
                "Email drafts are from Neon V2. Sign them '- Neon V2'; do not impersonate or sign as Mike.",
                "Never claim you added or changed the Calendar. Mike is the only Calendar editor.",
                "If Mike says he will add an event, phrase the draft as Mike will add it, not that it is already being added.",
                "A send request is allowed only when a complete current draft was already displayed in prior state and Mike clearly approves it.",
                "If Mike says something is on the Calendar, compare that claim to the supplied Calendar status.",
                "Return JSON only with keys: reply (string), draft (object or null), send_current_draft (boolean).",
                "A draft object has: to (string list), subject (string), body (string).",
                "",
                email_context,
                "",
                f"Calendar verification: {calendar_status}",
                "",
                f"Current conversation state: {json.dumps(state, ensure_ascii=True)}",
                "",
                f"Mike: {message}",
            ]
        )

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"history": []}
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"history": []}
        return value if isinstance(value, dict) else {"history": []}

    def _save_state(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
