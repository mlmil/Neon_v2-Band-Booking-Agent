import email
import imaplib
import json
from dataclasses import dataclass
from email.header import decode_header
from pathlib import Path


@dataclass(frozen=True)
class EmailMessage:
    sender_name: str
    sender_email: str
    subject: str
    date: str
    message_id: str
    body: str


class NeonEmailProvider:
    def __init__(self, config_path: Path | None = None, active_email_path: Path | None = None) -> None:
        self.config_path = config_path or Path.home() / ".hermes" / "skills" / "Neon_v1" / "smtp_config.json"
        self.active_email_path = active_email_path or Path.home() / ".hermes" / "neon_active_booking_email.json"

    def latest_actionable(self) -> EmailMessage | None:
        active = self._active_email()
        if active is not None:
            return active
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        mail = imaplib.IMAP4_SSL(config.get("imap_host", "imap.gmail.com"), config.get("imap_port", 993))
        mail.login(config["email"], config["app_password"])
        mail.select("INBOX", readonly=True)
        try:
            status, data = mail.search(None, "ALL")
            if status != "OK" or not data[0]:
                return None
            for uid in reversed(data[0].split()[-100:]):
                fetch_status, payload = mail.fetch(uid, "(BODY.PEEK[])")
                if fetch_status != "OK" or not payload or not isinstance(payload[0], tuple):
                    continue
                message = email.message_from_bytes(payload[0][1])
                sender = _decode(message.get("From", ""))
                if not any(value in sender.lower() for value in ("rockstarentertainment805", "thebikeguyiv", "jefftl123", "dukes")):
                    continue
                return EmailMessage(
                    sender_name=sender.split("<", 1)[0].strip().strip('"'),
                    sender_email=_address(sender),
                    subject=_decode(message.get("Subject", "")),
                    date=message.get("Date", ""),
                    message_id=message.get("Message-ID", "").strip(),
                    body=_body(message),
                )
        finally:
            mail.close()
            mail.logout()
        return None

    def _active_email(self) -> EmailMessage | None:
        if not self.active_email_path.exists():
            return None
        try:
            value = json.loads(self.active_email_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(value, dict):
            return None
        required = ("sender_name", "sender_email", "subject", "date", "message_id", "body")
        if not all(isinstance(value.get(key), str) for key in required):
            return None
        return EmailMessage(**{key: value[key] for key in required})


def _decode(value: str) -> str:
    return "".join(
        part.decode(charset or "utf-8", errors="replace") if isinstance(part, bytes) else part
        for part, charset in decode_header(value)
    )


def _address(sender: str) -> str:
    if "<" in sender and ">" in sender:
        return sender.split("<", 1)[1].split(">", 1)[0].strip()
    return sender.strip()


def _body(message: email.message.Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
    payload = message.get_payload(decode=True)
    return payload.decode(message.get_content_charset() or "utf-8", errors="replace").strip() if payload else ""
