#!/usr/bin/env python3
"""Neon Blonde inbox monitor — checks for new emails and flags actionable ones via Gmail IMAP."""
from __future__ import annotations

import argparse
import email as email_lib
import imaplib
import json
import os
import re
import smtplib
import sys
import time
from datetime import datetime, timezone
from email.header import decode_header
from email.mime.text import MIMEText
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.intake_receipt_tool import DEFAULT_RECEIPT_DIR, build_intake_receipt, write_intake_receipt
from scripts.booking_email_notifier import BookingEmailNotifier

DEFAULT_STATE_PATH = Path("data/intake/processed-gmail-imap.json")
DEFAULT_THREAD_CASE_DIR = Path("data/intake/threads")
DEFAULT_SMTP_CONFIG = Path(
    os.environ.get("NEON_SMTP_CONFIG", REPO_ROOT / ".secrets" / "smtp_config.json")
).expanduser()
BOT_SEND_ADDRESS = "neonblondevc+neonv2@gmail.com"

ACTION_KEYWORDS = [
    "gig", "booking", "contract", "date", "venue", "festival", "schedule",
    "confirm", "tentative", "deposit", "wedding", "rockstar", "tony",
    "sewer", "leashless", "fig mountain", "fox wine", "parque", "bombay",
    "garage", "ventura", "santa barbara", "ojai", "goleta", "solstice",
    "avocado", "lemon", "birthday party", "play that party", "how much",
    "how much do you charge",
]

VIP_SENDERS = [
    "thebikeguyiv",
    "rockstarentertainment",
    "jefftl123",
    "4lfred20",
    "sin.chonies.inc",
]


def redact_secrets(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"(?i)(password\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(bearer\s+)([A-Za-z0-9\-\._~\+\/]+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(token\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(AKIA[0-9A-Z]{16})", r"[REDACTED]", text)
    return text


def load_smtp_config(path: Path) -> dict:
    if not path.exists():
        print(f"SMTP config not found: {path}", file=sys.stderr)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"SMTP config parse error: {e}", file=sys.stderr)
        return {}


def should_skip_message(sender: str, subject: str) -> bool:
    s = sender.lower()
    if "noreply" in s or "no-reply" in s:
        return True
    if "calendar-notification@google.com" in s:
        return True
    return "neonblondevc@gmail.com" in s and (
        "daily check" in subject.lower() or "status report" in subject.lower() or "payout" in subject.lower()
    )


def build_flagged_email(
    sender: str,
    subject: str,
    date_str: str,
    body: str,
    message_id: str | None = None,
) -> dict | None:
    if should_skip_message(sender, subject):
        return None
    combined = f"{subject} {body} {sender}".lower()
    is_vip = any(v in sender.lower() for v in VIP_SENDERS)
    has_keyword = any(k in combined for k in ACTION_KEYWORDS)
    if not (is_vip or has_keyword):
        return None
    redacted_body = redact_secrets(body)
    return {
        "sender": sender,
        "subject": subject,
        "date": date_str,
        "message_id": message_id,
        "vip": is_vip,
        "body": redacted_body,
        "preview": redacted_body[:200] if redacted_body else "(no body)",
    }


def decode_str(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


def get_body_from_message(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode("utf-8", errors="replace")
                    text = re.sub(r"<[^>]+>", " ", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    return text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""


def fetch_gmail_thread(
    mail,
    *,
    thread_id: str,
    account_email: str,
    max_messages: int = 60,
) -> list[dict]:
    """Return chronological incoming and sent messages for one Gmail thread."""
    if not thread_id:
        return []
    status, _ = mail.select('"[Gmail]/All Mail"', readonly=True)
    if status != "OK":
        return []
    status, data = mail.search(None, "X-GM-THRID", thread_id)
    if status != "OK" or not data or not data[0]:
        return []
    messages = []
    for mid in data[0].split()[-max_messages:]:
        status, msg_data = mail.fetch(mid, "(BODY.PEEK[])")
        if status != "OK":
            continue
        raw = next(
            (part[1] for part in msg_data if isinstance(part, tuple) and len(part) > 1),
            None,
        )
        if not raw:
            continue
        msg = email_lib.message_from_bytes(raw)
        sender = decode_str(msg.get("From", ""))
        recipients = decode_str(msg.get("To", ""))
        body = redact_secrets(get_body_from_message(msg))
        messages.append(
            {
                "from": sender,
                "to": recipients,
                "subject": decode_str(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "message_id": msg.get("Message-ID", ""),
                "direction": "sent" if account_email.lower() in sender.lower() else "received",
                "text": body,
            }
        )
    return messages


def fetch_flagged_messages_imap(
    *,
    config: dict,
    processed_ids: set[str],
    max_results: int,
) -> tuple[int, list[dict]]:
    """Fetch unread inbox messages via IMAP and return actionable ones."""
    email_addr = config.get("email", "")
    app_password = config.get("app_password", "")
    imap_host = config.get("imap_host", "imap.gmail.com")
    imap_port = config.get("imap_port", 993)
    flagged = []
    new_count = 0

    if not email_addr or not app_password:
        print("  [Gmail] credentials missing", file=sys.stderr)
        return 0, []

    # Gmail can briefly stall during IMAP connection/login.  Bound each
    # attempt and retry transient socket/IMAP failures before giving up.
    timeout_seconds = int(config.get("imap_timeout_seconds", 30))
    retries = max(1, int(config.get("imap_retries", 3)))
    last_error = None
    for attempt in range(retries):
        try:
            mail = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=timeout_seconds)
            mail.login(email_addr, app_password)
            break
        except (OSError, imaplib.IMAP4.error) as e:
            last_error = e
            if attempt + 1 < retries:
                time.sleep(min(2 ** attempt, 8))
    else:
        print(f"  [Gmail] IMAP connection failed after {retries} attempts: {last_error}", file=sys.stderr)
        return 0, []

    try:
        mail.select("INBOX")
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            mail.logout()
            return 0, []

        msg_ids = data[0].split()[-max_results:]

        for mid in msg_ids:
            uid = mid.decode()
            # Get UID for dedup
            _, uid_data = mail.fetch(mid, "(UID X-GM-THRID)")
            message_id = uid
            gmail_thread_id = ""
            if uid_data and uid_data[0]:
                uid_raw = uid_data[0]
                if isinstance(uid_raw, tuple):
                    uid_bytes = b" ".join(part for part in uid_raw if isinstance(part, bytes))
                else:
                    uid_bytes = uid_raw
                uid_match = re.search(rb"UID (\d+)", uid_bytes)
                if uid_match:
                    message_id = f"imap:{email_addr}:{uid_match.group(1).decode()}"
                thread_match = re.search(rb"X-GM-THRID (\d+)", uid_bytes)
                if thread_match:
                    gmail_thread_id = thread_match.group(1).decode()

            if message_id in processed_ids:
                continue

            # BODY.PEEK preserves the user's unread state while still fetching
            # the complete RFC822 message payload.
            _, msg_data = mail.fetch(mid, "(BODY.PEEK[])")
            raw = msg_data[0][1] if msg_data and msg_data[0] and isinstance(msg_data[0], tuple) else None
            if not raw:
                continue

            msg = email_lib.message_from_bytes(raw)
            sender = decode_str(msg.get("From", ""))
            subject = decode_str(msg.get("Subject", "(no subject)"))
            date_str = msg.get("Date", "")
            body = get_body_from_message(msg)
            thread_messages = fetch_gmail_thread(
                mail,
                thread_id=gmail_thread_id,
                account_email=email_addr,
            )
            mail.select("INBOX", readonly=True)

            if should_skip_message(sender, subject):
                processed_ids.add(message_id)
                continue

            new_count += 1
            flagged.append({
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "message_id": message_id,
                "vip": any(v in sender.lower() for v in VIP_SENDERS),
                "body": redact_secrets(body),
                "preview": redact_secrets(body)[:200] if body else "(no body)",
                "gmail_thread_id": gmail_thread_id,
                "thread_messages": thread_messages,
                "thread_message_count": len(thread_messages),
            })

        mail.logout()
    except Exception as e:
        print(f"  [Gmail] IMAP error: {e}", file=sys.stderr)
        raise RuntimeError(f"Gmail IMAP unavailable: {e}") from e

    return new_count, flagged


def mark_messages_seen(config: dict) -> None:
    """Mark all UNSEEN messages in the inbox as SEEN (archive them visually)."""
    email_addr = config.get("email", "")
    app_password = config.get("app_password", "")
    imap_host = config.get("imap_host", "imap.gmail.com")
    imap_port = config.get("imap_port", 993)
    if not email_addr or not app_password:
        return
    try:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port)
        mail.login(email_addr, app_password)
        mail.select("INBOX")
        status, data = mail.search(None, "UNSEEN")
        if status == "OK" and data[0]:
            for mid in data[0].split():
                mail.store(mid, "+FLAGS", "\\SEEN")
        mail.logout()
    except Exception as e:
        print(f"  [Gmail] mark-seen error: {e}", file=sys.stderr)


def send_email_smtp(
    config: dict,
    to: str,
    subject: str,
    body: str,
) -> bool:
    """Send an email via SMTP using the bot's plus-alias as From."""
    email_addr = config.get("email", "")
    app_password = config.get("app_password", "")
    smtp_host = config.get("smtp_host", "smtp.gmail.com")
    smtp_port = config.get("smtp_port", 587)
    if not email_addr or not app_password:
        print("  [SMTP] credentials missing", file=sys.stderr)
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = f"Neon V2 <{BOT_SEND_ADDRESS}>"
        msg["To"] = to
        msg["Subject"] = subject
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(email_addr, app_password)
            server.send_message(msg)
        print(f"  -> SMTP sent to {to}")
        return True
    except Exception as e:
        print(f"  [SMTP] send error: {e}", file=sys.stderr)
        return False


def create_intake_receipts_for_flagged(flagged: list[dict], receipt_dir: Path = DEFAULT_RECEIPT_DIR) -> list[Path]:
    paths = []
    for item in flagged:
        receipt = build_intake_receipt(
            email_text=item.get("body") or "",
            sender=item.get("sender") or "",
            subject=item.get("subject") or "",
            source_date=item.get("date") or "",
            message_id=item.get("message_id"),
        )
        if "email_text" in receipt:
            del receipt["email_text"]
        path = write_intake_receipt(receipt, receipt_dir)
        paths.append(path)
    return paths


def load_processed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_processed_id(path: Path, msg_id: str) -> None:
    if not msg_id:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    processed = load_processed_ids(path)
    processed.add(msg_id)
    with path.open("w", encoding="utf-8") as f:
        json.dump({"processed_ids": list(processed), "last_updated": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def process_flagged_messages(
    flagged: list[dict],
    *,
    receipt_dir: Path,
    state_path: Path,
    thread_case_dir: Path = DEFAULT_THREAD_CASE_DIR,
    notifier=None,
) -> list[Path]:
    receipt_paths = []
    for item in flagged:
        receipt = build_intake_receipt(
            email_text=item.get("body") or "",
            sender=item.get("sender") or "",
            subject=item.get("subject") or "",
            source_date=item.get("date") or "",
            message_id=item.get("message_id"),
        )
        path = write_intake_receipt(receipt, receipt_dir)
        thread_case_dir.mkdir(parents=True, exist_ok=True)
        case_key = item.get("gmail_thread_id") or re.sub(
            r"[^A-Za-z0-9._-]+", "-", str(item.get("message_id") or "email-case")
        ).strip("-")
        case_path = thread_case_dir / f"{case_key}.json"
        case_path.write_text(
            json.dumps(
                {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "sender": item.get("sender"),
                    "subject": item.get("subject"),
                    "latest_message_id": item.get("message_id"),
                    "gmail_thread_id": item.get("gmail_thread_id"),
                    "latest_body": item.get("body"),
                    "thread_message_count": item.get("thread_message_count"),
                    "thread_messages": item.get("thread_messages") or [],
                    "send_status": "draft_not_created",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        item["case_path"] = str(case_path)
        if notifier is not None:
            result = notifier(item)
            if result.get("status") != "sent":
                raise RuntimeError("Telegram booking notification failed")
        receipt_paths.append(path)
        if item.get("message_id"):
            save_processed_id(state_path, item["message_id"])
    return receipt_paths


def print_report(new_count: int, flagged: list[dict], receipt_paths: list[Path] | None = None) -> None:
    if not flagged:
        print(f"No new actionable emails. ({new_count} total new since last check)")
        return
    print(f"FLAGGED {len(flagged)} of {new_count} new emails:\n")
    for item in flagged:
        tag = "VIP" if item["vip"] else "ACTION"
        print(f"{tag} FROM: {item['sender']}")
        print(f"   SUBJECT: {item['subject']}")
        print(f"   DATE: {item['date']}")
        print(f"   PREVIEW: {item['preview'][:150]}")
        if item.get("case_path"):
            print(f"   THREAD CASE: {item['case_path']}")
        print()
    if receipt_paths:
        print("INTAKE RECEIPTS WRITTEN:")
        for path in receipt_paths:
            print(f"   {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Neon Gmail inbox for actionable booking emails.")
    parser.add_argument("--write-intake-receipts", action="store_true")
    parser.add_argument("--notify-telegram", action="store_true")
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--thread-case-dir", default=str(DEFAULT_THREAD_CASE_DIR))
    parser.add_argument("--max-results", type=int, default=50)
    parser.add_argument("--mark-seen", action="store_true", default=False,
                        help="Explicitly mark all unread Gmail messages as SEEN (default: off)")
    parser.add_argument("--smtp-config", default=str(DEFAULT_SMTP_CONFIG),
                        help="Path to smtp_config.json for Neon Blonde Gmail")
    args = parser.parse_args()

    state_path = Path(args.state_path)
    processed_ids = load_processed_ids(state_path)

    smtp_config_path = Path(args.smtp_config)
    config = load_smtp_config(smtp_config_path)
    if not config:
        print("Gmail unavailable: could not load SMTP config", file=sys.stderr)
        return 1

    try:
        new_count, flagged = fetch_flagged_messages_imap(
            config=config,
            processed_ids=processed_ids,
            max_results=args.max_results,
        )
    except Exception as exc:
        print(f"Gmail unavailable: {exc}", file=sys.stderr)
        return 1

    # Persist seen message IDs to avoid re-processing
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({
            "processed_ids": list(processed_ids),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }, indent=2),
        encoding="utf-8",
    )

    receipt_paths = []
    if args.write_intake_receipts and flagged:
        notifier = BookingEmailNotifier.from_defaults().notify if args.notify_telegram else None
        try:
            receipt_paths = process_flagged_messages(
                flagged,
                receipt_dir=Path(args.receipt_dir),
                state_path=state_path,
                thread_case_dir=Path(args.thread_case_dir),
                notifier=notifier,
            )
        except Exception as e:
            print(f"Failed to process booking email: {e}", file=sys.stderr)
            return 1

    # Mark messages as SEEN so they don't reappear
    if args.mark_seen:
        mark_messages_seen(config)

    print_report(new_count, flagged, receipt_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
