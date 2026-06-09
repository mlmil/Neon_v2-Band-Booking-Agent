# IMAP & Sent Mail Patterns for Neon Blonde

> ⚠️ This file contains the detailed IMAP patterns that were moved from SKILL.md to make room for skill updates. The SKILL.md now has one-line pointers to this file.

## IMAP Connection

```python
import imaplib, json
from pathlib import Path

with open(str(Path.home() / '.hermes' / 'skills' / 'Neon_v2' / 'smtp_config.json')) as f:
    cfg = json.load(f)

mail = imaplib.IMAP4_SSL(cfg['imap_host'], cfg['imap_port'])
mail.login(cfg['email'], cfg['app_password'])
mail.select("INBOX")
```

Config file: `~/.hermes/skills/Neon_v2/smtp_config.json`

## Sent Mail Search via IMAP

Gmail's IMAP requires specific quoting for the Sent Mail folder name.

### Working pattern

```python
import imaplib, json, email
from email import policy
from pathlib import Path

with open(str(Path.home() / '.hermes' / 'skills' / 'Neon_v2' / 'smtp_config.json')) as f:
    cfg = json.load(f)

mail = imaplib.IMAP4_SSL(cfg['imap_host'], cfg['imap_port'])
mail.login(cfg['email'], cfg['app_password'])

# ⚠️ Must use escaped quotes around the Gmail folder name
mail.select('"[Gmail]/Sent Mail"')

# Search by keyword + date range
status, data = mail.search(None, '(SUBJECT "Harry" SINCE "7-May-2026")')
if status == 'OK' and data[0]:
    msg_id = data[0].split()[-1]  # latest message
    s_full, data = mail.fetch(msg_id, '(RFC822)')
    if s_full == 'OK':
        msg = email.message_from_bytes(data[0][1], policy=policy.default)
        print(f"Subject: {msg['Subject']}")
        print(f"To: {msg['To']}")
        print(f"Date: {msg['Date']}")
        # Get plaintext body (handles MIME, base64, quoted-printable)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_content()
                    break
        else:
            body = msg.get_content()

mail.logout()
```

### Why RFC822 instead of BODY.PEEK[TEXT]

Gmail sent mail bodies are consistently MIME-encoded (base64 or quoted-printable). `BODY.PEEK[TEXT]` returns the raw encoded bytes — you'd need to manually decode base64 and handle quoted-printable. **`RFC822` fetch + `email.message_from_bytes(policy=policy.default)` decodes everything transparently** — you get clean plaintext with no manual decoding.

```python
# DON'T: BODY.PEEK[TEXT] + manual base64 decode
s_b, body = mail.fetch(msg_id, '(BODY.PEEK[TEXT])')
raw = body[0][1]
try:
    text = base64.b64decode(raw).decode('utf-8')  # fragile
except Exception:
    text = raw.decode('utf-8', errors='replace')

# DO: RFC822 + email.message_from_bytes — handles all MIME encoding
s_full, data = mail.fetch(msg_id, '(RFC822)')
msg = email.message_from_bytes(data[0][1], policy=policy.default)
# body is clean plaintext, already decoded
```

### Key points
- Sent Mail folder name: `'"[Gmail]/Sent Mail"'` (single-quote the whole thing, double-quotes inside)
- **Prefer `(RFC822)` fetch + `email.message_from_bytes()`** — handles all MIME decoding automatically
- Use `BODY.PEEK` for quick header scans (won't download entire message body)
- `SUBJECT` search is most reliable; `TO`/`FROM` searches also work
- Headers-only fetch for quick scans: `'(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])'`

## ⚠️ Pitfall — IMAP Fetch Body Syntax

`mail.fetch(msg_id, '(BODY[TEXT] 0.2000)')` triggers a `BAD [b'Could not parse command']` error from Gmail's IMAP server.

**Fix**: Use `(BODY.PEEK[TEXT])` instead of `(BODY[TEXT] ...)`. The `BODY.PEEK` variant also avoids marking the message as seen.

```python
# DON'T: BODY[TEXT] with size range — triggers Gmail parse error
status, msg_data = mail.fetch(msg_id, '(BODY[TEXT] 0.2000)')

# DO: BODY.PEEK[TEXT] — no size range, works reliably
status, msg_data = mail.fetch(msg_id, '(BODY.PEEK[TEXT])')

# For headers + body in one call:
status, msg_data = mail.fetch(msg_id, '(RFC822.HEADER BODY.PEEK[TEXT])')
```

**To get headers and body separately**:
```python
# Get headers
status_hdr, hdr_data = mail.fetch(msg_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
# Get body (does not mark as read)
status_body, body_data = mail.fetch(msg_id, '(BODY.PEEK[TEXT])')
```

**Note**: When fetching individual header fields, use `FIELDS` (plural) — singular `FIELD` triggers a parse error.

## ⚠️ Pitfall — IMAP Compound Search Criteria

Complex compound criteria (e.g., `'(OR FROM "a" OR FROM "b")'`) can trigger a `BAD [b'Could not parse command']` error.

**Fix**: Use separate single-criteria searches instead of combining into one query, then merge results in Python.

```python
# DON'T: complex OR queries
status, data = mail.search(None, '(OR FROM "a" OR FROM "b")')

# DO: separate searches
results = set()
for addr in ["rockstarentertainment805", "dave@dukesbeachgrill"]:
    status, data = mail.search(None, f'FROM "{addr}"')
    if data[0]:
        results.update(data[0].split())
```

## ⚠️ Pitfall — Apostrophes in IMAP Search Terms

When using an f-string to build an IMAP search criterion that contains an apostrophe (e.g., searching for `Tony's`), Python's string quoting conflicts with the IMAP syntax.

```python
# 🔴 SyntaxError: f-string: unmatched '('
status, data = mail.search(None, f'(SUBJECT "Tony\'s" SINCE "7-May-2026")')
```

**Fix — use a variable or alternative quoting**:
```python
# ✅ Use a variable to separate the search term from the f-string
search_term = "Tony's"
status, data = mail.search(None, f'(SUBJECT "{search_term}" SINCE "7-May-2026")')

# ✅ Or use .format() instead of f-string
status, data = mail.search(None, '(SUBJECT "{}" SINCE "7-May-2026")'.format("Tony's"))
```

**Affects**: Any venue or contact name containing an apostrophe: `Tony's`, `Duke's`, `Harry's`, etc.

## Per-Contact Booking Email Sweep

More reliable than a compound OR query (Gmail IMAP chokes on complex `OR FROM` expressions):

```python
for addr in ["rockstarentertainment805", "jefftl123", "dave@dukesbeachgrill", "thebikeguyiv", "sin.chonies.inc"]:
    status, data = mail.search(None, f'(FROM "{addr}" SINCE "{date_since}")')
```

## SMTP Send

```python
import smtplib
# Use smtp_config.json credentials with smtplib.SMTP
with smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port']) as s:
    s.starttls()
    s.login(cfg['email'], cfg['app_password'])
    s.sendmail(from_addr, to_addrs, msg.as_string())
```
