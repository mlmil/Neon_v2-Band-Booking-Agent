#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.agentmail_health_check import DEFAULT_INBOX, agentmail_request, run_health_check


DEFAULT_SIGNATURE = "- Neon V2"


def _split_recipients(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _ensure_signature(text: str) -> str:
    stripped = text.rstrip()
    if stripped.endswith(DEFAULT_SIGNATURE):
        return stripped
    return f"{stripped}\n\n{DEFAULT_SIGNATURE}"


def build_send_payload(*, to: list[str], cc: list[str], subject: str, text: str) -> dict:
    return {
        "to": to,
        "cc": cc,
        "subject": subject.strip(),
        "text": _ensure_signature(text),
    }


def build_fallback_draft(payload: dict, *, reason_code: str) -> dict:
    return {
        "status": "gmail_draft_required",
        "reason_code": reason_code,
        "draft": {
            "to": ",".join(payload["to"]),
            "cc": ",".join(payload.get("cc", [])),
            "subject": payload["subject"],
            "body": payload["text"],
        },
    }


def summarize_send_result(*, http_status: int, body: dict, payload: dict, inbox: str) -> dict:
    if http_status != 200:
        return {
            "status": "blocked",
            "code": "AGENTMAIL_SEND_FAILED",
            "http_status": http_status,
            "inbox": inbox,
            "to": payload["to"],
            "cc": payload.get("cc", []),
            "subject": payload["subject"],
            "error": body,
        }
    return {
        "status": "sent",
        "http_status": http_status,
        "inbox": inbox,
        "to": payload["to"],
        "cc": payload.get("cc", []),
        "subject": payload["subject"],
        "message_id": body.get("message_id"),
        "thread_id": body.get("thread_id"),
    }


def send_agentmail(
    *,
    inbox: str,
    to: list[str],
    cc: list[str],
    subject: str,
    text: str,
    api_key: str | None = None,
    fallback_gmail_draft: bool = False,
) -> dict:
    api_key = api_key or os.environ.get("AGENTMAIL_API_KEY")
    payload = build_send_payload(to=to, cc=cc, subject=subject, text=text)
    health = run_health_check(api_key=api_key, required_inbox=inbox)
    if health["status"] != "success":
        blocked = {
            "status": "blocked",
            "code": "AGENTMAIL_HEALTH_CHECK_FAILED",
            "health": health,
            "to": to,
            "cc": cc,
            "subject": subject,
        }
        if fallback_gmail_draft:
            blocked["fallback"] = build_fallback_draft(payload, reason_code=blocked["code"])
        return blocked
    http_status, body = agentmail_request(api_key, f"/v0/inboxes/{inbox}/messages/send", payload=payload)
    receipt = summarize_send_result(http_status=http_status, body=body, payload=payload, inbox=inbox)
    receipt["key"] = health.get("key")
    if receipt["status"] != "sent" and fallback_gmail_draft:
        receipt["fallback"] = build_fallback_draft(payload, reason_code=receipt.get("code", "AGENTMAIL_SEND_FAILED"))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a Neon V2 operational email through AgentMail.")
    parser.add_argument("--inbox", default=DEFAULT_INBOX)
    parser.add_argument("--to", required=True, help="Comma-separated recipient email addresses.")
    parser.add_argument("--cc", default="", help="Comma-separated CC email addresses.")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--fallback-gmail-draft", action="store_true")
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--text")
    body_group.add_argument("--text-file")
    args = parser.parse_args()

    text = args.text if args.text is not None else Path(args.text_file).read_text()
    result = send_agentmail(
        inbox=args.inbox,
        to=_split_recipients(args.to),
        cc=_split_recipients(args.cc),
        subject=args.subject,
        text=text,
        fallback_gmail_draft=args.fallback_gmail_draft,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "sent" else 1


if __name__ == "__main__":
    raise SystemExit(main())
