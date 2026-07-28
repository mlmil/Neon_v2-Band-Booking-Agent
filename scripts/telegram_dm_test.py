#!/usr/bin/env python3
"""Send a private Telegram delivery test to approved Neon Blonde members."""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERMES_ROOT = Path("/Users/cthulhu/.hermes")
PROFILES = ("neon-v2", "neon-co_pilot")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api(profile: str, method: str, fields: dict[str, str]) -> dict:
    env = read_env(HERMES_ROOT / "profiles" / profile / ".env")
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError(f"{profile}: Telegram token is not configured")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=urllib.parse.urlencode(fields).encode(),
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(result.get("description", f"{profile}: {method} failed"))
    return result["result"]


def approved_members() -> dict[str, str]:
    members: dict[str, str] = {}
    for profile in PROFILES:
        path = HERMES_ROOT / "profiles" / profile / "platforms/pairing/telegram-approved.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for user_id, record in data.items():
            members[user_id] = record.get("user_name", "Band member")
    return members


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", action="append", help="Limit the test to this approved Telegram ID")
    parser.add_argument("--dry-run", action="store_true", help="Show recipients without sending")
    args = parser.parse_args()
    members = approved_members()
    if args.user_id:
        requested = set(args.user_id)
        members = {user_id: name for user_id, name in members.items() if user_id in requested}
    if not members:
        raise SystemExit("No approved Telegram members found")

    test_id = time.strftime("%Y%m%d-%H%M%S")
    results = []
    for profile in PROFILES:
        label = "Neon V2" if profile == "neon-v2" else "Gig Co-Pilot"
        for user_id, user_name in members.items():
            text = (
                f"DELIVERY TEST — {label}\n\n"
                "If you received this private message, reply exactly: TEST RECEIVED\n"
                f"Test ID: {test_id}"
            )
            result = {"profile": profile, "bot": label, "user_id": user_id, "user_name": user_name}
            if args.dry_run:
                result["status"] = "dry_run"
            else:
                sent = api(profile, "sendMessage", {"chat_id": user_id, "text": text})
                result["status"] = "accepted_by_telegram"
                result["message_id"] = str(sent.get("message_id", ""))
            results.append(result)
    print(json.dumps({"test_id": test_id, "results": results}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
