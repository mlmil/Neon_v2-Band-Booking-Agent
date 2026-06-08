#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB = Path("/Users/studio_hub/Desktop/Neon Blonde Skill/neon-blonde-booking/.communication_db.json")


def load_db(path: Path):
    if not path.exists():
        return {"emails": []}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"ERROR: Invalid JSON in communication database {path}: {e.msg} at line {e.lineno}, column {e.colno}."
        )
    if "emails" not in data:
        data["emails"] = []
    return data


def main():
    parser = argparse.ArgumentParser(description="Log a sent email to the local communication database.")
    parser.add_argument("--to", required=True)
    parser.add_argument("--cc", default="")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    data = load_db(args.db)
    data["emails"].append({
        "direction": "sent",
        "to": args.to,
        "cc": args.cc,
        "subject": args.subject,
        "body": args.body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    args.db.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.db.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except OSError as e:
        raise SystemExit(f"ERROR: Failed to write communication database {args.db}: {e}")

    print(f"Logged sent email to {args.db}")


if __name__ == "__main__":
    main()
