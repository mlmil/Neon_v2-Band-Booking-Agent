#!/usr/bin/env python3
"""Approve pending bot users who are verified members of the Neon Blonde group."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from onboard_telegram_member import HERMES_ROOT, PROFILES, approve, read_env, verify_group_member

CONFIRMATION = (
    "You're approved for Neon Blonde bot access. "
    "Please send Hello once so this bot can confirm your private chat is ready."
)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Refusing to modify malformed pairing file: {path}") from exc


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{path.stem}-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def pending_users() -> dict[str, str]:
    users: dict[str, str] = {}
    for profile in PROFILES:
        path = HERMES_ROOT / "profiles" / profile / "platforms/pairing/telegram-pending.json"
        for request in read_json(path).values():
            user_id = str(request.get("user_id", "")).strip()
            if user_id.isdigit():
                users[user_id] = str(request.get("user_name", "")).strip() or "Band member"
    return users


def clear_pending(user_id: str) -> None:
    for profile in PROFILES:
        path = HERMES_ROOT / "profiles" / profile / "platforms/pairing/telegram-pending.json"
        data = read_json(path)
        filtered = {
            request_id: request
            for request_id, request in data.items()
            if str(request.get("user_id", "")).strip() != user_id
        }
        if filtered != data:
            write_json(path, filtered)


def send_confirmation(profile: str, user_id: str) -> None:
    env = read_env(HERMES_ROOT / "profiles" / profile / ".env")
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError(f"{profile} Telegram token is unavailable")
    payload = urllib.parse.urlencode({"chat_id": user_id, "text": CONFIRMATION}).encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(result.get("description", f"{profile} confirmation failed"))


def process(*, notify: bool) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for user_id, user_name in pending_users().items():
        try:
            status = verify_group_member(user_id)
        except PermissionError as exc:
            results.append({"user_id": user_id, "result": "not_group_member", "detail": str(exc)})
            continue
        except Exception as exc:
            results.append({"user_id": user_id, "result": "verification_error", "detail": str(exc)})
            continue

        for profile in PROFILES:
            approve(profile, user_id, user_name)
        clear_pending(user_id)

        notification_errors = []
        if notify:
            for profile in PROFILES:
                try:
                    send_confirmation(profile, user_id)
                except Exception as exc:
                    notification_errors.append(f"{profile}: {exc}")
        results.append(
            {
                "user_id": user_id,
                "user_name": user_name,
                "result": "approved",
                "status": status,
                "notification": "sent" if not notification_errors else "; ".join(notification_errors),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()

    lock_path = HERMES_ROOT / "profiles/neon-v2/platforms/pairing/neon-onboarding.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"skipped": "already_running"}))
            return 0
        print(json.dumps({"processed": process(notify=not args.no_notify)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
