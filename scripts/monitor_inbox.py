#!/usr/bin/env python3
"""Neon Blonde inbox monitor — checks for new emails and flags actionable ones."""
import imaplib
import email
import json
import os
import sys
from email.header import decode_header
from datetime import datetime, timedelta, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = SKILL_DIR + "/smtp_config.json"
STATE_PATH = SKILL_DIR + "/.last_check.json"

# Load config
with open(CONFIG_PATH) as f:
    cfg = json.load(f)

USER = cfg["email"]
PASS = cfg["app_password"]

# Load last check timestamp
last_check = None
if os.path.exists(STATE_PATH):
    with open(STATE_PATH) as f:
        state = json.load(f)
        last_check = state.get("last_check_utc")

# Connect
mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login(USER, PASS)
mail.select("INBOX")

# Search since last check
if last_check:
    # Format: DD-Mon-YYYY
    since_date = datetime.fromisoformat(last_check).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE "{since_date}")')
else:
    # First run — last 24 hours
    status, messages = mail.search(None, "ALL")
    msg_ids = messages[0].split()
    recent = msg_ids[-30:] if len(msg_ids) > 30 else msg_ids
    messages = (None, recent)

msg_ids = messages[0].split() if messages[0] else []

# Keywords that signal a booking-related email
ACTION_KEYWORDS = [
    "gig", "booking", "contract", "date", "venue", "festival",
    "schedule", "confirm", "tentative", "deposit", "wedding",
    "rockstar", "tony", "sewer", "leashless", "fig mountain",
    "fox wine", "parque", "bombay", "garage", "ventura", "santa barbara",
    "ojai", "goleta", "solstice", "avocado", "lemon",
]

VIP_SENDERS = [
    "thebikeguyiv", "rockstarentertainment", "jefftl123",
    "4lfred20", "sin.chonies.inc",
]

new_count = 0
flagged = []

for mid in msg_ids:
    status, data = mail.fetch(mid, "(RFC822)")
    msg = email.message_from_bytes(data[0][1])
    
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8", errors="replace")
    
    sender = str(msg["From"] or "")
    date_str = str(msg["Date"] or "")
    
    # Skip our own sent mail and daily checks
    if "neonblondevc@gmail.com" in sender.lower():
        if "Daily Check" in subject or "STATUS REPORT" in subject:
            continue
    
    # Get body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode(errors="replace")
                except:
                    pass
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode(errors="replace")
        except:
            pass
    
    combined = (subject + " " + body + " " + sender).lower()
    
    is_vip = any(v in sender.lower() for v in VIP_SENDERS)
    has_keyword = any(k in combined for k in ACTION_KEYWORDS)
    
    if is_vip or has_keyword:
        flagged.append({
            "sender": sender,
            "subject": subject,
            "date": date_str,
            "vip": is_vip,
            "preview": body[:200] if body else "(no body)"
        })
    
    new_count += 1

mail.logout()

# Save new timestamp
now_utc = datetime.now(timezone.utc).isoformat()
with open(STATE_PATH, "w") as f:
    json.dump({"last_check_utc": now_utc}, f)

# Output
if not flagged:
    print(f"No new actionable emails. ({new_count} total new since last check)")
else:
    print(f"FLAGGED {len(flagged)} of {new_count} new emails:\n")
    for f_ in flagged:
        tag = "🔴 VIP" if f_["vip"] else "🟡"
        print(f"{tag} FROM: {f_['sender']}")
        print(f"   SUBJECT: {f_['subject']}")
        print(f"   DATE: {f_['date']}")
        print(f"   PREVIEW: {f_['preview'][:150]}")
        print()
