#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any


AGENTMAIL_BASE_URL = "https://api.agentmail.to"
DEFAULT_INBOX = "neon_blonde@agentmail.to"


def fingerprint_key(api_key: str | None) -> dict:
    if not api_key:
        return {"present": False}
    return {
        "present": True,
        "length": len(api_key),
        "sha256_prefix": hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12],
    }


def parse_inbox_emails(body: Any) -> list[str]:
    if isinstance(body, list):
        inboxes = body
    elif isinstance(body, dict):
        inboxes = body.get("inboxes") or body.get("data") or []
    else:
        inboxes = []
    emails = []
    for inbox in inboxes:
        if not isinstance(inbox, dict):
            continue
        email = inbox.get("email") or inbox.get("id") or inbox.get("inboxId")
        if email:
            emails.append(email)
    return emails


def summarize_list_inboxes_result(*, http_status: int, body: Any, required_inbox: str) -> dict:
    inboxes = parse_inbox_emails(body)
    if http_status != 200:
        return {
            "status": "blocked",
            "code": "AGENTMAIL_AUTH_FAILED",
            "http_status": http_status,
            "inboxes": inboxes,
        }
    if required_inbox not in inboxes:
        return {
            "status": "blocked",
            "code": "AGENTMAIL_INBOX_MISSING",
            "http_status": http_status,
            "required_inbox": required_inbox,
            "inboxes": inboxes,
        }
    return {
        "status": "success",
        "http_status": http_status,
        "required_inbox": required_inbox,
        "inboxes": inboxes,
    }


def agentmail_request(api_key: str, endpoint: str, *, payload: dict | None = None) -> tuple[int, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{AGENTMAIL_BASE_URL}{endpoint}",
        data=data,
        method="GET" if payload is None else "POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(text)
        except json.JSONDecodeError:
            body = {"raw": text[:500]}
        return exc.code, body


def run_health_check(
    *,
    api_key: str | None = None,
    required_inbox: str = DEFAULT_INBOX,
    send_test_to: str | None = None,
) -> dict:
    api_key = api_key or os.environ.get("AGENTMAIL_API_KEY")
    key_info = fingerprint_key(api_key)
    if not api_key:
        return {"status": "blocked", "code": "AGENTMAIL_API_KEY_MISSING", "key": key_info}

    list_status, list_body = agentmail_request(api_key, "/v0/inboxes")
    summary = summarize_list_inboxes_result(
        http_status=list_status,
        body=list_body,
        required_inbox=required_inbox,
    )
    summary["key"] = key_info
    if summary["status"] != "success" or not send_test_to:
        summary["send_test"] = "not_requested"
        return summary

    send_status, send_body = agentmail_request(
        api_key,
        f"/v0/inboxes/{required_inbox}/messages/send",
        payload={
            "to": [send_test_to],
            "subject": "[Neon V2] AgentMail health check",
            "text": "AgentMail send test from Neon V2.\n\n- Neon V2",
        },
    )
    if send_status != 200:
        summary.update(
            {
                "status": "blocked",
                "code": "AGENTMAIL_SEND_FAILED",
                "send_http_status": send_status,
                "send_error": send_body,
            }
        )
        return summary
    summary.update(
        {
            "send_test": "success",
            "send_http_status": send_status,
            "message_id": send_body.get("message_id"),
            "thread_id": send_body.get("thread_id"),
        }
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify AgentMail auth and Neon Blonde inbox access.")
    parser.add_argument("--inbox", default=DEFAULT_INBOX)
    parser.add_argument("--send-test-to", help="Optional explicit recipient for a live send test.")
    args = parser.parse_args()
    result = run_health_check(required_inbox=args.inbox, send_test_to=args.send_test_to)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
