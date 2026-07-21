#!/usr/bin/env python3
"""Read the most recent Neon Blonde Gmail messages without changing read state."""
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


def fetch_recent(config: dict, limit: int = 5) -> list[dict]:
    address = config.get("email", "")
    password = config.get("app_password", "")
    if not address or not password:
        raise RuntimeError("Neon Gmail credentials are missing")

    mail = imaplib.IMAP4_SSL(
        config.get("imap_host", "imap.gmail.com"),
        int(config.get("imap_port", 993)),
    )
    try:
        mail.login(address, password)
        status, _ = mail.select("INBOX", readonly=True)
        if status != "OK":
            raise RuntimeError("Unable to open Neon Gmail inbox")
        status, data = mail.search(None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []

        results = []
        for message_number in reversed(data[0].split()[-limit:]):
            status, payload = mail.fetch(message_number, "(BODY.PEEK[])")
            if status != "OK":
                continue
            raw = next(
                (part[1] for part in payload if isinstance(part, tuple) and len(part) > 1),
                None,
            )
            if not raw:
                continue
            message = email_lib.message_from_bytes(raw)
            body = redact_secrets(get_body_from_message(message))
            results.append(
                {
                    "from": decode_str(message.get("From", "")),
                    "to": decode_str(message.get("To", "")),
                    "subject": decode_str(message.get("Subject", "(no subject)")),
                    "date": message.get("Date", ""),
                    "preview": " ".join(body.split())[:500] or "(no text body)",
                }
            )
        return results
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--smtp-config", default=str(DEFAULT_SMTP_CONFIG))
    args = parser.parse_args()
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")

    config = load_smtp_config(Path(args.smtp_config).expanduser())
    print(json.dumps(fetch_recent(config, args.limit), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
