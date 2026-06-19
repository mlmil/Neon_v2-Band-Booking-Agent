# Neon V2 Automation Inventory

Updated: June 10, 2026

## Overview

Neon V2 currently has four scheduled macOS LaunchAgents. They run local wrapper
scripts from this repository. The wrappers prevent overlapping runs, load
protected environment settings, run deterministic Python scripts, and write
local logs or receipts.

None of these scheduled jobs sends email, changes Google Calendar, publishes
the Band Sheet, updates WordPress, changes payment status, or confirms a
booking.

## Automation Summary

| Automation | Schedule | Source Trigger | Main Script | Reads From | Writes To |
|---|---:|---|---|---|---|
| Gmail intake | Every 15 minutes | macOS LaunchAgent | `scripts/monitor_inbox.py` | Neon Blonde Gmail through read-only IMAP | `data/intake/receipts/`, `data/intake/processed-gmail.json` |
| GroupMe sync | Hourly | macOS LaunchAgent | `scripts/fetch_groupme_messages.py`, then `scripts/sync_groupme_messages.py` | GroupMe API | `data/groupme/messages/`, `data/groupme/groupme_db.json` |
| Unified health check | Hourly | macOS LaunchAgent | `scripts/neon_health_check.py` | AgentMail, public Band Sheet, public calendar, public website, dashboard data, LM Studio | `data/health/receipt_*.json` |
| Venue folder sync | Hourly | macOS LaunchAgent | `scripts/local_venue_folder_sync.py` | Public Neon Blonde calendar and LM Studio | `/Volumes/VADER/Manifold/Neon_Blonde/Venues/` |

All automation logs are written under:

```text
logs/automation/
```

## 1. Gmail Intake

### What starts it

LaunchAgent:

```text
com.neonblonde.gmail_intake
```

Schedule:

```text
Every 900 seconds (15 minutes)
```

LaunchAgent source:

```text
launch_agents/com.neonblonde.gmail_intake.plist
```

Installed copy:

```text
~/Library/LaunchAgents/com.neonblonde.gmail_intake.plist
```

### Execution chain

```text
LaunchAgent
  -> scripts/automation/wrapper_gmail_intake.sh
  -> scripts/monitor_inbox.py --write-intake-receipts
  -> scripts/intake_email_parser.py
  -> scripts/intake_receipt_tool.py
```

### Source data

- Neon Blonde Gmail inbox.
- Authentication comes from the existing IMAP configuration.
- The mailbox is opened read-only.
- Messages are fetched with `BODY.PEEK`, which must not mark them read or
  modify labels.

### Local output

```text
data/intake/receipts/
data/intake/processed-gmail.json
logs/automation/gmail_intake.log
```

The processed-message file prevents duplicate receipts.

### Current status

- Loaded and running on schedule.
- Last exit code: `0`.
- Five recorded runs in the current LaunchAgent session.

### Current concern

The receipt folder contains likely false positives, including WordPress and
website marketing messages. The keyword filter is operational but too broad.
These receipts should be reviewed before Gmail intake is connected to the
dashboard approval queue.

## 2. GroupMe Fetch And Sync

### What starts it

LaunchAgent:

```text
com.neonblonde.groupme_sync
```

Schedule:

```text
Every 3,600 seconds (hourly)
```

LaunchAgent source:

```text
launch_agents/com.neonblonde.groupme_sync.plist
```

### Execution chain

```text
LaunchAgent
  -> scripts/automation/wrapper_groupme_sync.sh
  -> scripts/fetch_groupme_messages.py
  -> GroupMe API
  -> individual message JSON files
  -> scripts/sync_groupme_messages.py
  -> combined searchable database
```

### Source data

- GroupMe API: `https://api.groupme.com/v3`
- Groups currently fetched:
  - Neon Blonde
  - Harrys
  - Potentials
  - Neon Blonde UPCOMING
  - Blackstar

### Local output

```text
data/groupme/messages/
data/groupme/groupme_db.json
logs/automation/groupme_sync.log
```

Current stored message count:

```text
1,273
```

The complete runtime folder is excluded from Git.

### Current status

- Loaded and running hourly.
- Last exit code: `0`.
- API authentication is working.
- Duplicate message files are skipped by GroupMe message ID.

## 3. Unified Health Check

### What starts it

LaunchAgent:

```text
com.neonblonde.health_check
```

Schedule:

```text
Every 3,600 seconds (hourly)
```

LaunchAgent source:

```text
launch_agents/com.neonblonde.health_check.plist
```

### Execution chain

```text
LaunchAgent
  -> scripts/automation/wrapper_health_check.sh
  -> scripts/neon_health_check.py
```

### Health sources

The unified check runs five isolated lanes:

| Lane | Script / Source | Purpose |
|---|---|---|
| AgentMail | `scripts/agentmail_health_check.py` | Confirms the Neon agent inbox is available |
| Band Sheet | `scripts/bandsheet_verification_report.py` | Compares published Band Sheet data with the public calendar |
| Website | `scripts/website_verification_report.py` | Compares public WordPress shows with the Band Sheet |
| Dashboard | `scripts/dashboard_server.py` data functions | Confirms dashboard files and Post-Gig data are available |
| LM Studio | `scripts/lm_studio_health_check.py` | Checks `http://127.0.0.1:1234/v1/models` and the configured model |

Each lane has its own failure boundary. One failed lane does not stop the other
checks.

### Local output

```text
data/health/receipt_<timestamp>.json
logs/automation/health_check.log
```

### Current status

- Loaded and running hourly.
- Last exit code: `0`.
- Latest receipt reports all five lanes successful.
- The health check performs no protected writes.

## 4. Venue Folder Sync

### What starts it

LaunchAgent:

```text
com.neonblonde.venue_sync
```

Schedule:

```text
Every 3,600 seconds (hourly)
```

LaunchAgent source:

```text
launch_agents/com.neonblonde.venue_sync.plist
```

### Execution chain

```text
LaunchAgent
  -> scripts/automation/wrapper_venue_sync.sh
  -> scripts/local_venue_folder_sync.py --sync-calendar --use-local-model
  -> public Neon Blonde calendar
  -> LM Studio digest request when a digest is missing
```

### Source data

- Public Neon Blonde Google Calendar iCal feed.
- LM Studio at `http://127.0.0.1:1234`.
- Default model: `gemma-4-e2b-it`.

### Local output

```text
/Volumes/VADER/Manifold/Neon_Blonde/Venues/<Venue>/<Venue - YYYY-MM-DD>/
```

Each gig folder may contain:

```text
LOCAL_GIG_RECEIPT.md
LOCAL_MODEL_DIGEST.md
```

Existing digest files are not overwritten.

### Current status

- Loaded and running hourly.
- Last exit code: `0`.
- Current venue folders were synchronized successfully.

## Shared Wrapper Behavior

Every wrapper:

1. Uses the Neon V2 repository as its working directory.
2. Uses a `/tmp` lock directory to prevent overlapping runs.
3. Loads `.secrets/neon-v2.env` when present.
4. Stops on script errors.
5. Writes output and errors to its automation log.

Lock directories:

```text
/tmp/neon_gmail_intake.lock
/tmp/neon_groupme_sync.lock
/tmp/neon_health_check.lock
/tmp/neon_venue_sync.lock
```

## Authentication Sources

| Service | Why It Is Used | Canonical Source |
|---|---|---|
| Gmail IMAP | Read-only booking intake | Existing Neon Gmail IMAP configuration |
| GroupMe | Fetch current group messages | `~/.neon_blonde/groupme_token` |
| AgentMail | Agent inbox health and approved sends | `.secrets/neon-v2.env` |
| WordPress | Approved public show updates | `.secrets/neon-v2.env` |
| Drive and Contacts | Private Neon Workspace data | `~/.config/gws` |
| Calendar | Read-only scheduling source | Public iCal feed; no authentication |
| LM Studio | Local digest generation and health | Local server; no authentication |

Secret values are not recorded in this report.

## What Is Not Automated

These actions still require Mike's explicit approval or manual action:

- Sending venue-facing email.
- Creating, editing, or deleting calendar events.
- Publishing Band Sheet changes.
- Updating WordPress show cards.
- Sharing venue portal files.
- Confirming bookings.
- Changing pay or booking terms.
- Marking payments complete.

## Runtime Data Locations

```text
data/intake/receipts/
data/intake/processed-gmail.json
data/groupme/messages/
data/groupme/groupme_db.json
data/health/
logs/automation/
```

Venue runtime data is stored outside the repository:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Venues/
```

## Current Assessment

The four scheduled automations are loaded and their latest runs completed
successfully.

The main issue requiring review is Gmail classification quality. The current
keyword filter has created receipts for marketing messages that are not booking
requests. The automation remains safe because it creates local receipts only,
but the filter should be tightened before those receipts drive dashboard
alerts or follow-up workflows.
