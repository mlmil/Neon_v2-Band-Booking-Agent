#!/usr/bin/env python3
"""Advance Telegram conflict scan checkpoints after a completed scan cycle."""
import json
import os
from datetime import datetime, timezone

BASE = "/Users/cthulhu/Desktop/Skill FIles/Neon_v2"

# Full-format checkpoint
full_path = os.path.join(BASE, "data/telegram/checkpoint.json")
with open(full_path) as f:
    full = json.load(f)

now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
full["last_scan_at"] = now_iso

with open(full_path, "w") as f:
    json.dump(full, f, indent=2)

print(f"Updated full checkpoint: last_scan_at -> {now_iso}")

# Simple-format checkpoint
simple_path = os.path.join(BASE, "checkpoints/telegram_conflict_scan.json")
with open(simple_path) as f:
    simple = json.load(f)

simple["last_check"] = now_iso
simple["scan_attempt"] = now_iso
simple["new_messages_found"] = False

with open(simple_path, "w") as f:
    json.dump(simple, f)

print(f"Updated simple checkpoint: scan_attempt -> {now_iso}, new_messages_found=false")
print("Done.")
