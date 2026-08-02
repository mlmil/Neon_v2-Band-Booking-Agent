#!/usr/bin/env python3
"""Telegram conflict scan for Neon V2 cron job.

Fetches recent updates from the authorized Neon Blonde group via Bot API,
checks for new operational claims, and compares with the Band Sheet.
"""
import json
import os
import sys
import urllib.request
import urllib.error

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GROUP_ID = "-1004424634571"
CHECKPOINT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "checkpoints",
    "telegram_conflict_scan.json"
)

def load_checkpoint():
    """Load the last checkpoint."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"last_check": None, "last_update_id": None}

def save_checkpoint(data):
    """Save checkpoint."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f)

def get_updates(offset=None, limit=50):
    """Fetch updates from Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = f"?limit={limit}"
    if offset:
        params += f"&offset={offset}"
    full_url = url + params
    req = urllib.request.Request(full_url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def main():
    checkpoint = load_checkpoint()
    last_update_id = checkpoint.get("last_update_id")
    
    # Fetch updates
    offset = last_update_id + 1 if last_update_id else None
    data = get_updates(offset=offset)
    
    if not data.get("ok"):
        print("ERROR: Telegram API returned not OK")
        print(json.dumps(data, indent=2))
        sys.exit(1)
    
    updates = data.get("result", [])
    
    if not updates:
        print("NO_NEW_UPDATES")
        # Still update the scan timestamp
        checkpoint["scan_attempt"] = __import__('datetime').datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        checkpoint["new_messages_found"] = False
        save_checkpoint(checkpoint)
        return
    
    # Find group messages
    group_messages = []
    for upd in updates:
        msg = upd.get("message", {}) or upd.get("channel_post", {}) or upd.get("edited_message", {})
        chat = msg.get("chat", {})
        if str(chat.get("id")) == GROUP_ID:
            group_messages.append({
                "update_id": upd["update_id"],
                "message_id": msg.get("message_id"),
                "date": msg.get("date"),
                "from": msg.get("from", {}).get("first_name", "Unknown"),
                "text": msg.get("text", ""),
            })
            if upd["update_id"] > (last_update_id or 0):
                last_update_id = upd["update_id"]
    
    if group_messages:
        print(f"FOUND {len(group_messages)} new group message(s):")
        for gm in group_messages:
            print(f"  [{gm['from']}] {gm.get('text', '(no text)')[:200]}")
        checkpoint["new_messages_found"] = True
    else:
        print("NO_GROUP_MESSAGES")
        checkpoint["new_messages_found"] = False
    
    checkpoint["last_update_id"] = last_update_id
    checkpoint["scan_attempt"] = __import__('datetime').datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    save_checkpoint(checkpoint)

if __name__ == "__main__":
    main()
