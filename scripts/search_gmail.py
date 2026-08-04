#!/usr/bin/env python3
"""Search Neon Blonde Gmail read-only without changing message state."""
from __future__ import annotations

import argparse
import email as email_lib
import imaplib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.monitor_inbox import (
    DEFAULT_SMTP_CONFIG,
    decode_str,
    get_body_from_message,
    load_smtp_config,
    redact_secrets,
)


def search_messages(config: dict, query: str, limit: int = 10, scan_limit: int = 200) -> list[dict]:
    address = config.get("email", "")
    password = config.get("app_password", "")
    if not address or not password:
        raise RuntimeError("Neon Gmail credentials are missing")

    mail = imaplib.IMAP4_SSL(config.get("imap_host", "imap.gmail.com"), int(config.get("imap_port", 993)))
    try:
        mail.login(address, password)
        status, _ = mail.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("Unable to open Neon Gmail inbox")
        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []

        needle = query.casefold().strip()
        matches = []
        for message_number in reversed(data[0].split()[-scan_limit:]):
            status, payload = mail.fetch(message_number, "(BODY.PEEK[])")
            if status != "OK":
                continue
            raw = next((part[1] for part in payload if isinstance(part, tuple) and len(part) > 1), None)
            if not raw:
                continue
            message = email_lib.message_from_bytes(raw)
            body = redact_secrets(get_body_from_message(message))
            item = {
                "from": decode_str(message.get("From", "")),
                "to": decode_str(message.get("To", "")),
                "subject": decode_str(message.get("Subject", "(no subject)")),
                "date": message.get("Date", ""),
                "preview": " ".join(body.split())[:700] or "(no text body)",
            }
            if needle in " ".join(item.values()).casefold():
                matches.append(item)
                if len(matches) >= limit:
                    break
        return matches
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Text to find in sender, recipient, subject, date, or body")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--scan-limit", type=int, default=200)
    parser.add_argument("--smtp-config", default=str(DEFAULT_SMTP_CONFIG))
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")
    if not 1 <= args.scan_limit <= 1000:
        parser.error("--scan-limit must be between 1 and 1000")
    config = load_smtp_config(Path(args.smtp_config).expanduser())
    print(json.dumps(search_messages(config, args.query, args.limit, args.scan_limit), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
