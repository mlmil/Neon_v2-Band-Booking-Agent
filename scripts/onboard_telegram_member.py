#!/usr/bin/env python3
"""Approve a verified Neon Blonde Telegram group member for both band bots."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERMES_ROOT = Path("/Users/cthulhu/.hermes")
GROUP_ID = "-1004424634571"
PROFILES = ("neon-v2", "neon-co_pilot")
MEMBER_STATUSES = {"creator", "administrator", "member", "restricted"}


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def verify_group_member(user_id: str) -> str:
    env = read_env(HERMES_ROOT / "profiles/neon-v2/.env")
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Neon V2 Telegram token is unavailable")
    query = urllib.parse.urlencode({"chat_id": GROUP_ID, "user_id": user_id})
    url = f"https://api.telegram.org/bot{token}/getChatMember?{query}"
    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.load(response)
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram membership check failed"))
    status = payload.get("result", {}).get("status", "")
    if status not in MEMBER_STATUSES:
        raise PermissionError(f"Telegram user is not an active band-group member ({status})")
    return status


def approve(profile: str, user_id: str, user_name: str) -> Path:
    directory = HERMES_ROOT / "profiles" / profile / "platforms/pairing"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "telegram-approved.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError:
        raise RuntimeError(f"Refusing to overwrite malformed pairing file: {path}")
    data[user_id] = {"user_name": user_name, "approved_at": time.time()}
    fd, temporary = tempfile.mkstemp(prefix="telegram-approved-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--user-name", default="Band member")
    args = parser.parse_args()
    user_id = args.user_id.strip()
    if not user_id.isdigit():
        parser.error("--user-id must come from Telegram sender metadata")
    status = verify_group_member(user_id)
    for profile in PROFILES:
        approve(profile, user_id, args.user_name.strip() or "Band member")
    print(json.dumps({"approved": True, "user_id": user_id, "status": status, "profiles": PROFILES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
