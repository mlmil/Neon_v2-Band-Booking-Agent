#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


DEFAULT_SOURCE = Path("/Volumes/VADER/Neon_Blonde/GroupMeChats/messages")
DEFAULT_DB = Path("/Volumes/VADER/Neon_Blonde/GroupMeChats/.groupme_db.json")


def load_existing(db_path: Path):
    if not db_path.exists():
        return {"messages": {}, "last_sync": None}
    try:
        with db_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"ERROR: Invalid JSON in existing database {db_path}: {e.msg} at line {e.lineno}, column {e.colno}."
        )
    if "messages" not in data:
        data["messages"] = {}
    return data


def main():
    parser = argparse.ArgumentParser(description="Sync GroupMe JSON exports into a local database.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"ERROR: GroupMe messages folder not found at {args.source}. Run fetch_groupme_messages.py first.")
    if not args.source.is_dir():
        raise SystemExit(f"ERROR: GroupMe source path is not a directory: {args.source}")

    data = load_existing(args.db)
    messages = data["messages"]
    added = 0

    for path in sorted(args.source.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as f:
                msg = json.load(f)
        except json.JSONDecodeError as e:
            print(
                f"ERROR: Skipping invalid JSON file {path}: {e.msg} at line {e.lineno}, column {e.colno}.",
                file=sys.stderr,
            )
            continue
        except OSError as e:
            print(f"ERROR: Skipping unreadable file {path}: {e}", file=sys.stderr)
            continue

        msg_id = str(msg.get("id") or path.stem)
        if msg_id in messages:
            continue

        messages[msg_id] = {
            "id": msg_id,
            "name": msg.get("name"),
            "text": msg.get("text"),
            "created_at": msg.get("created_at"),
            "sender_id": msg.get("sender_id"),
            "group_id": msg.get("group_id"),
            "system": msg.get("system", False),
            "source_path": str(path),
        }
        added += 1

    data["last_sync"] = datetime.now(timezone.utc).isoformat()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.db.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except OSError as e:
        raise SystemExit(f"ERROR: Failed to write GroupMe database {args.db}: {e}")

    print(f"Synced {added} new messages into {args.db}")


if __name__ == "__main__":
    main()
