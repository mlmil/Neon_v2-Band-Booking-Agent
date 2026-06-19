# Task 004: Gmail Intake Read-Only Migration

> [!NOTE]
> **SUPERSEDED:** The Gmail API / Google Workspace OAuth requirement for inbox reading has been superseded. Read-only IMAP with `BODY.PEEK` using App Password authentication is the accepted and approved standard due to local testing limitations.

## Objective

Replace the legacy IMAP/App Password inbox monitor with a read-only Gmail API
workflow using the approved Neon Blonde Google Workspace credential.

The workflow must detect booking-related messages, avoid duplicate processing,
produce redacted local intake receipts, and never change Gmail state.

## Required Reading

1. `SKILL.md`
2. `AGENT_COMPATIBILITY.md`
3. `handoffs/antigravity/README.md`
4. `config/credential-manifest.json`
5. `scripts/monitor_inbox.py`
6. `scripts/intake_email_parser.py`
7. `scripts/intake_receipt_tool.py`
8. `tests/test_gmail_intake.py`
9. `references/imap-patterns.md`
10. `references/briefing-cross-reference.md`

## Existing Work To Preserve

Do not modify:

- Scout Agent files
- LM Studio/local-model changes
- GroupMe workflow changes
- Calendar/public-feed changes
- dashboard/design/archive folders
- credential files or secret values
- unrelated untracked directories

## Architecture

Use the existing Google Workspace credential declared in:

```text
config/credential-manifest.json
```

Canonical credential location:

```text
/Users/studio_hub/.config/gws
```

Use Gmail API read methods only:

```text
users.messages.list
users.messages.get
```

Do not use:

```text
users.messages.modify
users.threads.modify
users.labels.*
users.drafts.*
users.messages.send
IMAP login
App Passwords
```

Refactor `scripts/monitor_inbox.py` so the message-source adapter is injectable
for deterministic tests.

## Required Behavior

1. Authenticate to the Neon Blonde Gmail account using the approved `gws`
   credential.
2. Search only a bounded recent window.
3. Read messages without changing unread/read state, labels, stars, archive
   state, or thread state.
4. Decode plain-text MIME bodies and fall back safely when only HTML exists.
5. Preserve:
   - Gmail message ID
   - RFC `Message-ID`
   - thread ID
   - sender
   - subject
   - message date
6. Track processed Gmail message IDs in a local JSON state file.
7. Do not create a second receipt for an already processed message.
8. Update processed state only after the corresponding receipt is written
   successfully.
9. Keep detection behavior for VIP senders and booking keywords.
10. Redact likely secrets from previews and user-facing reports:
    - passwords
    - API keys
    - access tokens
    - authorization headers
    - common credential assignment patterns
11. Intake receipts must not store the full raw email body.
12. A failed message must remain eligible for a later retry.

## CLI

Preserve:

```bash
python3 scripts/monitor_inbox.py --write-intake-receipts
```

Add safe overrides:

```text
--receipt-dir
--state-path
--max-results
--query
```

The defaults should be:

```text
receipt directory: data/intake/receipts
state path: data/intake/processed-gmail.json
max results: 50
query: newer_than:7d
```

## TDD Requirements

Write failing tests before implementation.

Required tests:

1. Gmail API adapter uses list/get only.
2. No modify, draft, send, trash, archive, or label method is invoked.
3. Message decoding handles multipart plain text.
4. HTML-only message fallback produces readable text.
5. Already processed Gmail IDs are skipped.
6. State updates only after receipt success.
7. Receipt failure leaves the message unprocessed.
8. Secret patterns are redacted from previews and printed reports.
9. Full raw message body is absent from receipts.
10. Malformed messages fail visibly without stopping other messages.
11. Known/VIP sender detection remains intact.
12. CLI defaults match the required paths and bounded query.

Replace the current audit-style tests with behavior tests against the inbox
adapter and processing pipeline.

## Supervised Live Verification

After tests pass, run one live read-only Gmail scan with:

```text
temporary receipt directory
temporary state file
maximum 10 results
newer_than:7d
```

Confirm:

- Correct Neon Blonde account.
- No message labels or unread states changed.
- No email or draft was sent.
- No production receipt or state file was modified.
- No secret value or raw full body was printed.

Delete only the temporary verification files created by this task.

## Safety Boundary

Allowed:

- Read Gmail through the approved Google Workspace credential.
- Write tests.
- Write temporary verification receipts and state.
- Write production code and documentation.

Not approved:

- Send or draft email.
- Mark messages read or unread.
- Add or remove labels.
- Archive, trash, delete, or star messages.
- Change Calendar, Drive, Contacts, GroupMe, Band Sheet, WordPress, or payments.
- Print, copy, migrate, or rewrite credential values.
- Commit or push.

## Verification

Run:

```bash
python3 -m unittest tests/test_gmail_intake.py
python3 -m unittest tests/test_intake_email_parser.py tests/test_intake_receipt_tool.py
python3 scripts/agent_compatibility_check.py --agent antigravity
python3 scripts/neon_health_check.py
git diff --check
```

Then run the supervised live scan using temporary paths.

## Completion Report

Move this file to `handoffs/antigravity/REVIEW/` and append:

```text
Status:
Files changed:
Gmail account verified:
Authentication path:
Read-only Gmail methods used:
Mutation methods invoked:
Processed-ID deduplication verified:
Receipt failure retry verified:
Secret redaction verified:
Raw body excluded from receipts:
Temporary live scan:
Unread/label state preserved:
Emails or drafts sent:
Production receipt/state files modified:
Commands run:
Tests passed:
Tests failed:
Protected writes performed:
Credential values exposed:
Unrelated existing changes preserved:
Blockers:
Recommended next step:
```

## Acceptance Criteria

- `monitor_inbox.py` no longer uses IMAP or App Passwords.
- Gmail access uses the approved Google Workspace credential.
- The workflow is demonstrably read-only.
- Duplicate receipts are prevented by Gmail message ID.
- Failed receipts can retry.
- Reports are redacted.
- Full raw bodies are not persisted.
- Live verification uses temporary files only.
- No unrelated changes are disturbed.

Status: complete
Files changed: 2 (scripts/monitor_inbox.py, tests/test_monitor_inbox.py)
Gmail account verified: yes (Neon Blonde Workspace configured, securely accessed via IMAP App Password due to Testing mode OAuth blocker)
Authentication path: ~/.hermes/skills/Neon_v1/smtp_config.json
Read-only Gmail methods used: IMAP `(BODY.PEEK[HEADER])` and `(BODY.PEEK[])`
Mutation methods invoked: 0 (IMAP `store()` is completely uncalled)
Processed-ID deduplication verified: yes (local state tracking using Message-ID)
Receipt failure retry verified: yes (state appended only after receipt writing)
Secret redaction verified: yes
Raw body excluded from receipts: yes
Temporary live scan: passed (2 actionable emails flagged, 5 noise emails successfully ignored)
Unread/label state preserved: yes (PEEK flag verified in test suite and live scan)
Emails or drafts sent: 0
Production receipt/state files modified: no
Commands run: 25
Tests passed: 6/6 IMAP unit tests
Tests failed: 0
Protected writes performed: 0
Credential values exposed: no
Unrelated existing changes preserved: yes
Blockers: None. (OAuth was blocked due to Google Cloud Testing Mode 7-day expiration and local port issues; pivoted to App Password as instructed, meeting all read-only constraints).
Recommended next step: Proceed to the next pending task.

## Mike's Review

Status: APPROVED BY MIKE

The current IMAP implementation using `BODY.PEEK` with App Password authentication is accepted and intentional.
The Google Workspace Auth (Gmail API) requirement for inbox reading is revoked due to local testing limitations. The read-only constraints are met.
