#!/usr/bin/env python3
"""
fetch_groupme_messages.py

Pulls messages from the GroupMe API and saves them as individual JSON files
into the local messages directory. Run this first, then sync_groupme_messages.py.

Usage:
    python3 fetch_groupme_messages.py
    python3 fetch_groupme_messages.py --token YOUR_TOKEN
    python3 fetch_groupme_messages.py --group-id 12345678

Token is read from (in order):
    1. --token argument
    2. GROUPME_TOKEN environment variable
    3. ~/.neon_blonde/groupme_token file
    4. smtp_config.json groupme_token field (if present)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import urllib.error

BASE_URL = "https://api.groupme.com/v3"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "groupme" / "messages"
TOKEN_FILE = Path.home() / ".neon_blonde" / "groupme_token"
SKILL_DIR = Path(__file__).parent.parent
SMTP_CONFIG = SKILL_DIR / "smtp_config.json"


def load_token(arg_token=None):
    if arg_token:
        return arg_token
    env_token = os.environ.get("GROUPME_TOKEN")
    if env_token:
        return env_token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    if SMTP_CONFIG.exists():
        try:
            cfg = json.loads(SMTP_CONFIG.read_text())
            if cfg.get("groupme_token"):
                return cfg["groupme_token"]
        except Exception:
            pass
    return None


def api_get(path, token, params=None):
    url = f"{BASE_URL}{path}?token={token}"
    if params:
        for k, v in params.items():
            url += f"&{k}={v}"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERROR: GroupMe API returned {e.code} for {path}: {e.reason}")
    except urllib.error.URLError as e:
        raise SystemExit(f"ERROR: Could not reach GroupMe API: {e.reason}")


def fetch_groups(token):
    data = api_get("/groups", token, {"per_page": 100})
    return data.get("response", [])


def fetch_messages(token, group_id, before_id=None, limit=100):
    params = {"limit": limit}
    if before_id:
        params["before_id"] = before_id
    data = api_get(f"/groups/{group_id}/messages", token, params)
    resp = data.get("response", {})
    return resp.get("messages", [])


def save_message(msg, output_dir, group_name):
    msg_id = str(msg.get("id", ""))
    if not msg_id:
        return False
    path = output_dir / f"{msg_id}.json"
    if path.exists():
        return False  # already saved, skip
    payload = {**msg, "group_name": group_name}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return True


def main():
    parser = argparse.ArgumentParser(description="Fetch GroupMe messages to local JSON files.")
    parser.add_argument("--token", help="GroupMe API access token")
    parser.add_argument("--group-id", help="Only fetch this group ID (default: all groups)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-messages", type=int, default=2000, help="Max messages per group")
    args = parser.parse_args()

    token = load_token(args.token)
    if not token:
        raise SystemExit(
            "ERROR: No GroupMe token found.\n"
            "  Options:\n"
            "    1. python3 fetch_groupme_messages.py --token YOUR_TOKEN\n"
            "    2. echo 'YOUR_TOKEN' > ~/.neon_blonde/groupme_token\n"
            "    3. export GROUPME_TOKEN=YOUR_TOKEN\n"
            "  Get your token at: https://dev.groupme.com/"
        )

    args.output.mkdir(parents=True, exist_ok=True)

    if args.group_id:
        groups = [{"id": args.group_id, "name": args.group_id}]
    else:
        print("Fetching groups...")
        groups = fetch_groups(token)
        print(f"Found {len(groups)} group(s):")
        for g in groups:
            print(f"  [{g['id']}] {g['name']}")

    total_saved = 0

    for group in groups:
        group_id = str(group["id"])
        group_name = group.get("name", group_id)
        print(f"\nFetching: {group_name}")

        before_id = None
        group_saved = 0
        fetched = 0

        while fetched < args.max_messages:
            messages = fetch_messages(token, group_id, before_id=before_id)
            if not messages:
                break

            for msg in messages:
                if save_message(msg, args.output, group_name):
                    group_saved += 1

            fetched += len(messages)
            before_id = messages[-1]["id"]
            print(f"  {fetched} fetched, {group_saved} new...", end="\r")
            time.sleep(0.3)

            if len(messages) < 100:
                break

        print(f"  Done: {group_saved} new messages saved.   ")
        total_saved += group_saved

    log_path = args.output.parent / "last_fetch.json"
    log_path.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "groups_fetched": len(groups),
        "new_messages_saved": total_saved,
        "output_dir": str(args.output),
    }, indent=2))

    print(f"\nTotal: {total_saved} new messages saved to {args.output}")


if __name__ == "__main__":
    main()
