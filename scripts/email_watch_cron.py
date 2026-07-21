#!/usr/bin/env python3
"""
Neon Blonde email monitor — tracks ALL email conversations.
Stays in the loop on every exchange: incoming, outgoing, replies, follow-ups.

Outputs JSON for the agent to summarize concisely.
"""

import imaplib
import email
import json
import os
import re
from email.header import decode_header
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMTP_CONFIG = os.path.expanduser(
    os.environ.get('NEON_SMTP_CONFIG', os.path.join(REPO_ROOT, '.secrets', 'smtp_config.json'))
)
STATE_FILE = os.path.expanduser(
    os.environ.get('NEON_EMAIL_WATCH_STATE', os.path.join(REPO_ROOT, 'data', 'intake', 'email_watch_state.json'))
)

SKIP_SENDERS = [
    'calendar-notification@google.com', 'no-reply@google.com',
    'noreply@google.com', 'no-reply@accounts.google.com',
    'payments-noreply@google.com',
    'mailer-daemon', 'postmaster', 'noreply@', 'no-reply@',
    'info@make.com', 'make.com',
]

MARKETING_SENDERS = [
    'mailchimp', 'campaign@', 'newsletter@', 'marketing@',
    'promo@', 'noreply@bandcamp.com', 'noreply@eventbrite.com',
    'noreply@facebookmail.com', 'noreply@instagram.com',
    'noreply@linkedin.com', 'noreply@medium.com',
    'updates@', 'team@', 'hello@',
]


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'seen_message_ids': [], 'pending_replies': {}}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def decode_mime_header(value):
    if not value:
        return ''
    decoded = ''
    for part, enc in decode_header(value):
        if isinstance(part, bytes):
            decoded += part.decode(enc or 'utf-8', errors='replace')
        else:
            decoded += part
    return decoded

def get_body(msg):
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == 'text/plain':
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='replace')
                    break
        if not body:
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == 'text/html':
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='replace')
                        body = re.sub(r'<[^>]+>', ' ', body)
                        body = re.sub(r'\s+', ' ', body).strip()
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode('utf-8', errors='replace')
    return body[:2000]

def extract_sender_name(from_addr):
    """Get just the name or email for display."""
    if '<' in from_addr:
        name = from_addr.split('<')[0].strip().strip('"')
        if name:
            return name
        email_addr = from_addr.split('<')[1].rstrip('>')
        return email_addr
    return from_addr

def get_base_subject(subject):
    """Strip Re:/Fwd: to get base subject for thread matching."""
    return re.sub(r'^(Re:|Fwd:)\s*', '', subject, flags=re.IGNORECASE).strip()

def is_from_mike(from_addr):
    """Check if email is from Neon Blonde (Mike)."""
    return 'neonblondevc@gmail.com' in from_addr.lower()


def main():
    with open(SMTP_CONFIG) as f:
        cfg = json.load(f)

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(cfg['email'], cfg['app_password'])

    # Get inbox messages
    mail.select('INBOX')
    status, data = mail.search(None, 'ALL')
    inbox_ids = data[0].split()
    recent_inbox = inbox_ids[-20:] if len(inbox_ids) >= 20 else inbox_ids

    # Get sent mail to track Mike's replies
    mail.select('"[Gmail]/Sent Mail"')
    status, sent_data = mail.search(None, 'ALL')
    sent_ids = sent_data[0].split()
    recent_sent = sent_ids[-15:] if len(sent_ids) >= 15 else sent_ids

    state = load_state()
    seen = set(state.get('seen_message_ids', []))
    pending = state.get('pending_replies', {})

    new_emails = []
    mike_replies = []

    # Check inbox for new incoming emails
    mail.select('INBOX')
    for mid in recent_inbox:
        mid_str = mid.decode() if isinstance(mid, bytes) else str(mid)
        if mid_str in seen:
            continue

        status, msg_data = mail.fetch(mid, '(RFC822)')
        for resp in msg_data:
            if isinstance(resp, tuple):
                msg = email.message_from_bytes(resp[1])
                frm = msg.get('From', '')
                subject = decode_mime_header(msg.get('Subject', ''))
                date_str = msg.get('Date', '')
                body = get_body(msg)
                has_unsub = msg.get('List-Unsubscribe') is not None
                from_lower = frm.lower()

                # Skip marketing and automated
                skip = False
                for s in SKIP_SENDERS + MARKETING_SENDERS:
                    if s in from_lower:
                        skip = True
                        break
                if has_unsub:
                    skip = True

                if skip:
                    seen.add(mid_str)
                    continue

                # This is an incoming email worth tracking
                sender = extract_sender_name(frm)
                is_mike = is_from_mike(frm)
                base_subj = get_base_subject(subject)

                # Check if Mike has replied to this
                replied = False
                mail.select('"[Gmail]/Sent Mail"')
                for smid in recent_sent:
                    status, sdata = mail.fetch(smid, '(BODY[HEADER.FIELDS (TO SUBJECT)])')
                    for sresp in sdata:
                        if isinstance(sresp, tuple):
                            sheaders = sresp[1].decode('utf-8', errors='replace')
                            sent_to = re.search(r'To:\s*(.*)', sheaders)
                            sent_subj = re.search(r'Subject:\s*(.*)', sheaders)
                            if sent_to and sent_subj:
                                to_addr = sent_to.group(1).strip().lower()
                                s_subj = get_base_subject(sent_subj.group(1).strip())
                                if sender.lower() in to_addr and base_subj.lower() in s_subj.lower():
                                    replied = True
                                    break
                    if replied:
                        break
                mail.select('INBOX')

                email_info = {
                    'from': sender,
                    'subject': subject,
                    'date': date_str,
                    'body_preview': body[:500],
                    'is_mike': is_mike,
                    'replied': replied,
                    'message_id': mid_str,
                }

                if is_mike:
                    # Mike sent an email — track as a reply
                    mike_replies.append(email_info)
                    # Remove from pending if it was there
                    pending.pop(base_subj, None)
                else:
                    new_emails.append(email_info)
                    if not replied:
                        pending[base_subj] = {
                            'from': sender,
                            'subject': subject,
                            'date': date_str,
                            'first_seen': datetime.now(timezone.utc).isoformat(),
                            'message_id': mid_str,
                        }
                    else:
                        pending.pop(base_subj, None)

                seen.add(mid_str)

    # Check pending replies for overdue (24h+)
    now = datetime.now(timezone.utc)
    overdue = []
    for subj, info in pending.items():
        try:
            first_seen = datetime.fromisoformat(info.get('first_seen', ''))
            age_hours = (now - first_seen).total_seconds() / 3600
        except Exception:
            age_hours = 0
        if age_hours > 24:
            overdue.append({
                'from': info['from'],
                'subject': info['subject'],
                'date': info['date'],
                'age_hours': round(age_hours, 1),
            })

    seen_list = list(seen)[-100:]
    state['seen_message_ids'] = seen_list
    state['pending_replies'] = pending
    state['last_check'] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    mail.logout()

    output = {
        'new_emails': new_emails,
        'mike_replies': mike_replies,
        'overdue_unreplied': overdue,
    }
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
