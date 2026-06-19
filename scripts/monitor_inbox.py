#!/usr/bin/env python3
"""Neon Blonde inbox monitor — checks for new emails and flags actionable ones using IMAP (Read-Only)."""
from __future__ import annotations

import argparse
import email
import imaplib
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.intake_receipt_tool import DEFAULT_RECEIPT_DIR, build_intake_receipt, write_intake_receipt
from scripts.booking_email_notifier import BookingEmailNotifier
from scripts.agentmail_health_check import DEFAULT_INBOX, agentmail_request

DEFAULT_STATE_PATH = Path("data/intake/processed-agentmail.json")

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
    # Redact common secrets patterns
    text = re.sub(r"(?i)(password\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(bearer\s+)([A-Za-z0-9\-\._~\+\/]+)", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)(token\s*[:=]\s*)(\S+)", r"\1[REDACTED]", text)
    text = re.sub(r"(AKIA[0-9A-Z]{16})", r"[REDACTED]", text)
    return text


def decode_mime(s: str | bytes | None) -> str:
    if not s:
        return ''
    parts = decode_header(s)
    return ''.join(
        p.decode(c or 'utf-8', errors='replace') if isinstance(p, bytes) else p
        for p, c in parts
    )


def get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode('utf-8', errors='replace')

        # Fallback HTML stripper if only html exists
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                payload = part.get_payload(decode=True)
                if payload:
                    html_data = payload.decode('utf-8', errors='replace')
                    text = re.sub(r"<[^>]+>", " ", html_data)
                    return re.sub(r"\s+", " ", text).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode('utf-8', errors='replace')
    return ''


def should_skip_message(sender: str, subject: str) -> bool:
    s = sender.lower()
    if "noreply" in s or "no-reply" in s:
        return True
    if "calendar-notification@google.com" in s:
        return True
    if "neon_blonde@agentmail.to" in s:
        return True
    return "neonblondevc@gmail.com" in s and (
        "daily check" in subject.lower() or "status report" in subject.lower()
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
        if notifier is not None:
            result = notifier(item)
            if result.get("status") != "sent":
                raise RuntimeError("Telegram booking notification failed")
        receipt_paths.append(path)
        if item.get("message_id"):
            save_processed_id(state_path, item["message_id"])
    return receipt_paths


def fetch_flagged_messages_agentmail(
    *,
    request,
    processed_ids: set[str],
    max_results: int,
) -> tuple[int, list[dict]]:
    inbox = urllib.parse.quote(DEFAULT_INBOX, safe="@")
    status, body = request(f"/v0/inboxes/{inbox}/messages?limit={max_results}")
    if status != 200 or not isinstance(body, dict):
        raise RuntimeError("AgentMail inbox request failed")
    messages = body.get("messages") or body.get("data") or []
    flagged = []
    new_count = 0
    for message in messages:
        if not isinstance(message, dict):
            continue
        message_id = str(message.get("message_id") or "")
        if message_id and message_id in processed_ids:
            continue
        sender = str(message.get("from") or "")
        subject = str(message.get("subject") or "")
        date_str = str(message.get("timestamp") or message.get("created_at") or "")
        body_text = str(message.get("text") or message.get("preview") or "")
        labels = message.get("labels") or []
        if "received" not in labels or should_skip_message(sender, subject):
            continue
        new_count += 1
        thread_id = str(message.get("thread_id") or "")
        thread_messages = []
        if thread_id:
            thread_status, thread = request(f"/v0/inboxes/{inbox}/threads/{urllib.parse.quote(thread_id, safe='')}")
            if thread_status == 200 and isinstance(thread, dict):
                thread_messages = thread.get("messages") or []
                for thread_message in reversed(thread_messages):
                    if str(thread_message.get("message_id") or "") == message_id:
                        body_text = str(
                            thread_message.get("text")
                            or thread_message.get("extracted_text")
                            or thread_message.get("preview")
                            or body_text
                        )
                        break
        flagged.append(
            {
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "message_id": message_id,
                "thread_id": thread_id,
                "thread_messages": thread_messages,
                "vip": any(v in sender.lower() for v in VIP_SENDERS),
                "body": redact_secrets(body_text),
                "preview": redact_secrets(body_text)[:200] if body_text else "(no body)",
            }
        )
    return new_count, flagged


def fetch_flagged_messages_imap(mail: imaplib.IMAP4_SSL, processed_ids: set[str], max_results: int) -> tuple[int, list[dict]]:
    status, data = mail.search(None, 'ALL')
    if status != 'OK' or not data[0]:
        return 0, []

    all_uids = data[0].split()
    msg_ids_to_check = all_uids[-max_results:]

    flagged = []
    fetched_count = 0

    for uid in msg_ids_to_check:
        # PEEK prevents marking as read
        s, d = mail.fetch(uid, '(BODY.PEEK[HEADER])')
        if s != 'OK' or not d or not d[0]:
            continue

        header_data = d[0][1] if isinstance(d[0], tuple) else None
        if not header_data:
            continue

        header_msg = email.message_from_bytes(header_data)
        msg_id = header_msg.get('Message-ID', '').strip()

        # Skip if we already processed this
        if msg_id and msg_id in processed_ids:
            continue

        fetched_count += 1

        # Fetch full message payload without marking read
        s2, d2 = mail.fetch(uid, '(BODY.PEEK[])')
        if s2 != 'OK' or not d2 or not d2[0]:
            continue

        full_data = d2[0][1] if isinstance(d2[0], tuple) else None
        if not full_data:
            continue

        msg = email.message_from_bytes(full_data)

        sender = decode_mime(msg.get('From', ''))
        subject = decode_mime(msg.get('Subject', ''))
        date_str = msg.get('Date', '')

        body = get_body(msg)

        item = build_flagged_email(
            sender=sender,
            subject=subject,
            date_str=date_str,
            body=body,
            message_id=msg_id,
        )
        if item:
            flagged.append(item)

    return fetched_count, flagged


def get_imap_client() -> imaplib.IMAP4_SSL:
    cfg_path = Path.home() / '.hermes' / 'skills' / 'Neon_v1' / 'smtp_config.json'
    if not cfg_path.exists():
        raise SystemExit(f"ERROR: SMTP config not found at {cfg_path}")

    with cfg_path.open() as f:
        cfg = json.load(f)

    mail = imaplib.IMAP4_SSL(cfg.get('imap_host', 'imap.gmail.com'), cfg.get('imap_port', 993))
    mail.login(cfg['email'], cfg['app_password'])
    mail.select('INBOX', readonly=True) # Extra safety for read-only
    return mail


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
        print()

    if receipt_paths:
        print("INTAKE RECEIPTS WRITTEN:")
        for path in receipt_paths:
            print(f"   {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Neon AgentMail for actionable booking emails.")
    parser.add_argument("--write-intake-receipts", action="store_true")
    parser.add_argument("--notify-telegram", action="store_true")
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--max-results", type=int, default=50)
    args = parser.parse_args()

    state_path = Path(args.state_path)
    processed_ids = load_processed_ids(state_path)

    api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        print("AgentMail unavailable: AGENTMAIL_API_KEY is missing", file=sys.stderr)
        return 1

    def request(endpoint: str):
        return agentmail_request(api_key, endpoint)

    try:
        new_count, flagged = fetch_flagged_messages_agentmail(
            request=request,
            processed_ids=processed_ids,
            max_results=args.max_results,
        )
    except Exception as exc:
        print(f"AgentMail unavailable: {exc}", file=sys.stderr)
        return 1

    receipt_paths = []
    if args.write_intake_receipts:
        notifier = BookingEmailNotifier.from_defaults().notify if args.notify_telegram else None
        try:
            receipt_paths = process_flagged_messages(
                flagged,
                receipt_dir=Path(args.receipt_dir),
                state_path=state_path,
                notifier=notifier,
            )
        except Exception as e:
            print(f"Failed to process booking email: {e}", file=sys.stderr)
            return 1

    print_report(new_count, flagged, receipt_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
