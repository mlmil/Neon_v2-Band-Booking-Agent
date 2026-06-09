#!/usr/bin/env python3
"""Neon Blonde inbox monitor — checks for new emails and flags actionable ones."""
from __future__ import annotations

import argparse
import email
import imaplib
import json
import sys
from datetime import datetime, timezone
from email.header import decode_header
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.intake_receipt_tool import DEFAULT_RECEIPT_DIR, build_intake_receipt, write_intake_receipt


CONFIG_PATH = REPO_ROOT / "smtp_config.json"
STATE_PATH = REPO_ROOT / ".last_check.json"

ACTION_KEYWORDS = [
    "gig",
    "booking",
    "contract",
    "date",
    "venue",
    "festival",
    "schedule",
    "confirm",
    "tentative",
    "deposit",
    "wedding",
    "rockstar",
    "tony",
    "sewer",
    "leashless",
    "fig mountain",
    "fox wine",
    "parque",
    "bombay",
    "garage",
    "ventura",
    "santa barbara",
    "ojai",
    "goleta",
    "solstice",
    "avocado",
    "lemon",
]

VIP_SENDERS = [
    "thebikeguyiv",
    "rockstarentertainment",
    "jefftl123",
    "4lfred20",
    "sin.chonies.inc",
]


def decode_subject(raw_subject: str | None) -> str:
    subject, encoding = decode_header(raw_subject or "")[0]
    if isinstance(subject, bytes):
        return subject.decode(encoding or "utf-8", errors="replace")
    return str(subject)


def extract_plain_text_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(errors="replace")
                except Exception:
                    return ""
        return ""
    try:
        return msg.get_payload(decode=True).decode(errors="replace")
    except Exception:
        return ""


def should_skip_message(sender: str, subject: str) -> bool:
    return "neonblondevc@gmail.com" in sender.lower() and (
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

    return {
        "sender": sender,
        "subject": subject,
        "date": date_str,
        "message_id": message_id,
        "vip": is_vip,
        "body": body,
        "preview": body[:200] if body else "(no body)",
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
        paths.append(write_intake_receipt(receipt, receipt_dir))
    return paths


def load_config(path: Path = CONFIG_PATH) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_last_check(path: Path = STATE_PATH) -> str | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f).get("last_check_utc")


def save_last_check(path: Path = STATE_PATH) -> None:
    path.write_text(json.dumps({"last_check_utc": datetime.now(timezone.utc).isoformat()}) + "\n", encoding="utf-8")


def fetch_flagged_messages(config: dict, last_check: str | None) -> tuple[int, list[dict]]:
    mail = imaplib.IMAP4_SSL(config.get("imap_host", "imap.gmail.com"), int(config.get("imap_port", 993)))
    try:
        mail.login(config["email"], config["app_password"])
        mail.select("INBOX")

        if last_check:
            since_date = datetime.fromisoformat(last_check).strftime("%d-%b-%Y")
            _status, messages = mail.search(None, f'(SINCE "{since_date}")')
        else:
            _status, messages = mail.search(None, "ALL")
            msg_ids = messages[0].split()
            recent = msg_ids[-30:] if len(msg_ids) > 30 else msg_ids
            messages = (None, recent)

        msg_ids = messages[0].split() if messages[0] else []
        flagged = []
        for mid in msg_ids:
            _status, data = mail.fetch(mid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            subject = decode_subject(msg["Subject"])
            sender = str(msg["From"] or "")
            date_str = str(msg["Date"] or "")
            body = extract_plain_text_body(msg)
            item = build_flagged_email(
                sender=sender,
                subject=subject,
                date_str=date_str,
                body=body,
                message_id=str(msg["Message-ID"] or ""),
            )
            if item:
                flagged.append(item)
        return len(msg_ids), flagged
    finally:
        mail.logout()


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
    parser = argparse.ArgumentParser(description="Check Neon Blonde inbox for actionable booking emails.")
    parser.add_argument("--write-intake-receipts", action="store_true")
    parser.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    args = parser.parse_args()

    config = load_config()
    last_check = load_last_check()
    new_count, flagged = fetch_flagged_messages(config, last_check)
    save_last_check()

    receipt_paths = []
    if args.write_intake_receipts:
        receipt_paths = create_intake_receipts_for_flagged(flagged, Path(args.receipt_dir))

    print_report(new_count, flagged, receipt_paths)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
