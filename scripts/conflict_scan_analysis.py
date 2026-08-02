#!/usr/bin/env python3
"""Analyze Telegram archive/checkpoint for new group messages since last scan."""
import json
import os
import sys
from datetime import datetime, timezone

BASE = "/Users/cthulhu/Desktop/Skill FIles/Neon_v2"
CHECKPOINT_PATH = os.path.join(BASE, "data/telegram/checkpoint.json")
ARCHIVE_PATH = os.path.join(BASE, "data/telegram/booking_watcher/archive.jsonl")
QUEUE_PATH = os.path.join(BASE, "data/telegram/booking_watcher/queue.jsonl")

# Read checkpoint
with open(CHECKPOINT_PATH) as f:
    checkpoint = json.load(f)

group_chat = checkpoint["chat_id"]  # "-1004424634571"
last_msg_id = checkpoint.get("last_message_id")
last_msg_date = checkpoint.get("last_message_date")
last_scan_at = checkpoint.get("last_scan_at")

print(f"Checkpoint: chat={group_chat}, last_msg_id={last_msg_id}, last_msg_date={last_msg_date} ({datetime.fromtimestamp(last_msg_date, tz=timezone.utc).isoformat()}), last_scan_at={last_scan_at}")

# Scan archive for new group messages
def scan_jsonl(path, label):
    if not os.path.exists(path):
        print(f"{label}: file not found")
        return []
    new_msgs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            chat_id = rec.get("chat_id")
            if str(chat_id) != group_chat:
                continue
            msg_id = rec.get("message_id")
            msg_date = rec.get("message_date", 0)
            sender = rec.get("sender_name", "")
            is_bot = any(tag in sender.lower() for tag in ["bot", "copilot"])
            # Must be newer than checkpoint date
            if msg_date > last_msg_date:
                new_msgs.append({
                    "id": msg_id,
                    "date": msg_date,
                    "sender": sender,
                    "is_bot": is_bot,
                    "text": rec.get("text", "")[:100],
                    "source": label
                })
    return new_msgs

archive_new = scan_jsonl(ARCHIVE_PATH, "archive")
queue_new = scan_jsonl(QUEUE_PATH, "queue")

all_new = archive_new + queue_new
print(f"\nArchive new group entries: {len(archive_new)}")
for m in archive_new:
    print(f"  id={m['id']}, date={m['date']} ({datetime.fromtimestamp(m['date'], tz=timezone.utc).isoformat()}), sender={m['sender']}, bot={m['is_bot']}, text={m['text']}")

print(f"\nQueue new group entries: {len(queue_new)}")
for m in queue_new:
    print(f"  id={m['id']}, date={m['date']}, sender={m['sender']}, bot={m['is_bot']}, text={m['text']}")

# Filter: exclude bot messages
human_new = [m for m in all_new if not m["is_bot"]]
print(f"\nNew human group messages since checkpoint: {len(human_new)}")

if human_new:
    print("QUALIFYING NEW MESSAGES FOUND")
    for m in human_new:
        print(f"  [{m['source']}] id={m['id']}, sender={m['sender']}: {m['text']}")
else:
    print("NO new qualifying human group messages since checkpoint")

print("\nExcluded bot/reply messages:")
for m in all_new:
    if m["is_bot"]:
        print(f"  [{m['source']}] id={m['id']}, date={m['date']}, sender={m['sender']}: {m['text']}")
