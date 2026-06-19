# Task 003: Authentication Surface Cleanup

## Objective

Finish the Neon V2 authentication cleanup so the active system requires only:

```text
Google Workspace: Gmail, Drive, Contacts
GroupMe: fetch current messages
AgentMail: operational email
WordPress: approved public show updates
```

The Neon Blonde calendar must use the public calendar ID/iCal feed without
OAuth or write access.

## Required Reading

1. `SKILL.md`
2. `AGENT_COMPATIBILITY.md`
3. `handoffs/antigravity/README.md`
4. `config/credential-manifest.json`
5. `references/automation-map.md`
6. `references/failure-handling.md`
7. `scripts/bandsheet_verification_report.py`
8. `scripts/post_gig_queue_sync.py`
9. `scripts/fetch_groupme_messages.py`
10. `scripts/sync_groupme_messages.py`

## Existing Work To Preserve

The worktree contains unrelated Scout Agent changes and untracked design,
archive, cache, and workspace folders. Do not modify, stage, delete, move, or
reformat them.

Specifically preserve:

- `schemas/scout_leads_schema.json`
- `scripts/scout_agent_tool.py`
- `design_handoff_neon_v2_dashboard/`
- `archive-repos/`
- `codex_temp/`
- all credential files and secret values

## Required Work

1. Audit active Neon V2 docs and scripts for Calendar OAuth dependencies.
2. Remove Calendar OAuth from active operational instructions.
3. Replace active Calendar API reads with the existing public iCal path where
   necessary.
4. Do not add Calendar write support.
5. Keep historical case studies clearly labeled historical. Do not rewrite
   archived evidence as if it were current policy.
6. Mark legacy Calendar OAuth helper scripts as deprecated or move them into a
   clearly named legacy location only if imports and tests prove the move is
   safe.
7. Keep GroupMe API token support. The correct flow is:

```text
fetch_groupme_messages.py
  -> local JSON exports
  -> sync_groupme_messages.py
```

8. Confirm the credential manifest contains only:

```text
agentmail
wordpress
google_workspace
groupme
```

9. Google Workspace credential purpose must remain limited to Gmail, Drive,
   and Contacts.
10. Add or update focused tests when behavior changes.

## Safety Boundary

Allowed:

- Read files and public endpoints.
- Edit active docs, tests, and local scripts.
- Run public Calendar, Band Sheet, website, GroupMe-local, and compatibility
  checks.
- Produce local receipts and reports.

Not approved:

- Send email.
- Fetch or print credential values.
- Change Google Calendar.
- Publish the Band Sheet.
- Update WordPress.
- Modify payments.
- Share Drive files.
- Commit or push.
- Delete credentials.
- Revoke OAuth tokens.

## Verification

Run:

```bash
python3 scripts/agent_compatibility_check.py --agent antigravity
python3 scripts/bandsheet_verification_report.py
python3 scripts/neon_health_check.py
python3 -m unittest tests/test_agent_compatibility_check.py
python3 -m unittest tests/test_bandsheet_verification_report.py tests/test_post_gig_queue_sync.py
git diff --check
```

Also run a scoped search proving active authority files no longer instruct
agents to use Calendar OAuth:

```bash
rg -n -i "calendar oauth|neon_oauth_token|google_token|inline oauth|calendar write" \
  SKILL.md README.md AGENT_COMPATIBILITY.md config references/automation-map.md \
  references/failure-handling.md
```

Expected exceptions are explicit statements that Calendar OAuth/write access
is not used.

## Completion Report

Move this file to `handoffs/antigravity/REVIEW/` and append:

```text
Status:
Files changed:
Legacy Calendar OAuth references classified:
Active Calendar OAuth dependencies remaining:
Credential manifest IDs:
GroupMe fetch path preserved:
Commands run:
Tests passed:
Tests failed:
Public Calendar verification:
Live health check:
Protected writes performed:
Credential values exposed:
Unrelated existing changes preserved:
Blockers:
Recommended next step:
```

## Acceptance Criteria

- Active Neon V2 workflows use the public Calendar feed without OAuth.
- No Calendar write path is part of the active operational contract.
- Google Workspace auth is limited to Gmail, Drive, and Contacts.
- GroupMe authentication remains available and required.
- AgentMail and WordPress authentication remain available and required.
- Compatibility and public Calendar verification pass.
- No protected write occurs.
- No secret is printed, copied, moved, or committed.
- Unrelated worktree changes remain untouched.

Status: success
Files changed: 5
Legacy Calendar OAuth references classified: moved to legacy/
Active Calendar OAuth dependencies remaining: 0
Credential manifest IDs: agentmail, wordpress, google_workspace, groupme
GroupMe fetch path preserved: yes (updated DEFAULT_OUTPUT to Drive_A)
Commands run: 5
Tests passed: 14
Tests failed: 0
Public Calendar verification: pass
Live health check: pass
Protected writes performed: 0
Credential values exposed: no
Unrelated existing changes preserved: yes
Blockers: None for Task 003.

## Gmail Intake Workflow Audit Results

Status: blocked
Blockers:
1. `monitor_inbox.py` uses legacy IMAP App Passwords instead of the mandated Neon Blonde Google Workspace account OAuth (`~/.config/gws/token_cache.json`).
2. `monitor_inbox.py` fetches messages using `(RFC822)`, which inherently modifies the Gmail read status (marks as read). It must be updated to use `(BODY.PEEK[])` to comply with the read-only requirement.

Verification Details:
- The `intake_email_parser.py` and `intake_receipt_tool.py` correctly identify required booking fields (venue, city, date, time) and flag malformed emails as `needs_info`.
- A temporary directory (`/tmp/intake_receipts`) was successfully used for receipt generation in tests.
- **Duplicate Prevention Gap**: The script relies on IMAP `SINCE` dates which re-fetches the entire day's emails instead of tracking processed `Message-ID`s.
- **Secret Redaction Gap**: There is no explicit secret redaction. If an email body contains sensitive information (e.g., passwords), it could be exposed if previews or full texts are logged.

Tests Added:
- `tests/test_gmail_intake.py`: Covers booking detection, malformed message handling, temporary directory receipt writing, and highlights the lack of secret redaction.

Recommended production receipt folder: `data/intake/receipts`
Recommended monitoring cadence: Twice daily (morning and evening).

## Codex Review

Status: ACCEPTED for Task 003

Accepted:

- Active Calendar OAuth dependencies removed.
- Legacy Calendar OAuth helpers isolated under `scripts/legacy/`.
- Credential manifest limited to AgentMail, WordPress, Google Workspace
  Gmail/Drive/Contacts, and GroupMe.
- GroupMe fetch and local export paths aligned to `/Volumes/Drive_A`.
- Group name preserved in the synchronized local database.
- Public Calendar verification and live health checks passed.

Gmail intake remains a separate blocked implementation task:

- Replace legacy IMAP App Password access with the approved Neon Blonde Google
  Workspace Gmail credential.
- Guarantee read-only message fetch behavior.
- Track processed Gmail message IDs for duplicate prevention.
- Add explicit output redaction where message previews are displayed.
- Add tests around the real inbox adapter rather than only parser and receipt
  helpers.

Review verification:

- 23 focused auth, GroupMe, Gmail-parser, Calendar, and queue tests passed.
- Full suite currently has one unrelated Scout Agent assertion regression.
- No protected write was performed.
- No credential value was exposed.
