# Neon V2 Automation Map

Use this reference to distinguish model reasoning, deterministic scripts, scheduled work, and approval-protected actions.

## Active Architecture

```text
Hermes / Neon V2 reasons, drafts, summarizes, and recommends.
Local scripts parse, validate, compare, and create private local receipts.
Gmail IMAP/SMTP provides booking email intake and approved sending.
Telegram provides band and operator messaging.
The public calendar is read-only.
Google Drive content is mirrored locally at NEON_DRIVE_ROOT.
Mike approves source-of-truth and external changes.
```

## Deterministic Scripts

| Script | Purpose |
|---|---|
| `scripts/monitor_inbox.py` | Read Gmail with IMAP, flag booking messages, and create intake receipts |
| `scripts/email_watch_cron.py` | Track new Gmail conversation activity and overdue replies |
| `scripts/intake_email_parser.py` | Parse booking details and missing fields without confirming a booking |
| `scripts/intake_receipt_tool.py` | Write private intake receipts |
| `scripts/bandsheet_verification_report.py` | Compare the public calendar with published Band Sheet data |
| `scripts/website_verification_report.py` | Compare public website shows with Band Sheet data |
| `scripts/local_venue_folder_sync.py` | Create venue and gig folders beneath `$NEON_DRIVE_ROOT/Venues` |
| `scripts/find_rehearsal_dates.py` | Find candidate rehearsal dates |
| `scripts/post_gig_queue_sync.py` | Activate closeout records after gigs |
| `scripts/post_gig_payout_tool.py` | Record payout and tip information in the private administrative ledger |
| `scripts/payout_csv_sync.py` | Reconcile payout data with calendar gigs |
| `scripts/post_gig_reminder.py` | Send approval-configured payout reminders through Gmail SMTP |
| `scripts/neon_health_check.py` | Run public calendar/Band Sheet and website verification lanes |
| `scripts/agent_compatibility_check.py` | Verify required local files and credentials without exposing secrets |

## Approval Gates

Mike's explicit approval is required before:

- Sending venue-facing email
- Publishing Band Sheet changes
- Updating WordPress
- Sharing private venue files
- Changing booking, cancellation, or pay terms
- Marking payment complete
- Broadcasting a booking or cancellation

Neon V2 never writes to Google Calendar. It drafts calendar changes for manual entry.

## Scheduling State

The Hermes `neon-v2` profile currently has no scheduled jobs. Do not describe Gmail monitoring, verification, venue sync, reminders, or health checks as automatic until the corresponding job is installed and smoke-tested.

## Retired Systems

The active Neon V2 architecture has no dependency on the former alternate chat platform, alternate email relay, previous workstation mounts, or experimental on-device model server. Do not recreate those dependencies or use their credentials as fallbacks.

## Ownership

Mike owns final booking decisions and protected approvals. Neon V2 owns operational routing, warnings, receipts, and drafts. Deterministic scripts own parsing and validation.
