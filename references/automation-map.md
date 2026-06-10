# Neon V2 Automation Map

Use this to understand what AI is doing, what local scripts are doing, what automation exists, and who is responsible for each layer.

## Purpose

Neon V2 should be transparent. Mike should be able to tell:

- Which model/agent is reasoning.
- Which local script is doing deterministic work.
- Which workflow is automated.
- Which actions require human approval.
- Which parts are experimental.

## Core Boundary

```text
AI can reason, draft, summarize, classify, and recommend.
Local scripts can validate, compare, parse, and generate local files.
Automation can monitor and remind.
Mike approves source-of-truth changes.
```

Protected writes:

- Google Calendar updates
- Band Sheet publish/deploy
- Venue-facing email send
- WordPress page updates
- Venue portal sharing
- Payment marked complete
- Booking marked confirmed
- Pay/rate terms changed

## AI / Agent Roles

| Agent / Model | Role | Allowed Work | Not Allowed Without Approval |
|---|---|---|---|
| Codex | Mastermind/orchestration layer and full operator | Design, engineering, checks, local workflows, and approved service actions | Protected writes without Mike approval |
| Claude | Independent verifier and full operator | Independent checks, reviews, local workflows, and approved service actions | Protected writes without Mike approval |
| Hermes Agent | Automation runner, operational bridge, and full operator | Scheduled checks, reminders, local workflows, and approved service actions | Protected writes without Mike approval |
| Antigravity | Available AI workspace/model lane | Future specialized work; role not finalized | Production ownership until defined |
| Local model | Experimental observer | Read-only digest, folder summaries, low-risk classification | Calendar, Band Sheet, email, payout, portal, or receipt writes |

Current assignment rule:

```text
Codex is the mastermind. Codex, Claude, and Hermes share credential/API parity and may operate Neon V2 within the same approval gates.
```

## Deterministic Local Scripts

These scripts should do predictable work and return structured output.

| Script | Purpose | Phase |
|---|---|---|
| `scripts/venue_agent_tool.py` | Validate calendar-shaped event data and produce venue/gig/receipt dry-run plan | Booking Phase |
| `scripts/intake_email_parser.py` | Parse booking-request email text into venue/date/time/city fields, missing-info flags, and an acknowledgment draft without booking anything | Intake Phase |
| `scripts/intake_receipt_tool.py` | Wrap parsed booking-request email text with source metadata and write a local Intake Phase receipt/task | Intake Phase |
| `scripts/scout_agent_tool.py` | Validate Scout Agent lead CSV structure and statuses | Intake / Scout |
| `scripts/local_venue_folder_sync.py` | Create local per-venue gig folders under `/Volumes/VADER/Manifold/Neon_Blonde/Venues` and write local receipt/model digest files without overwriting existing digests | Booking Phase / Local Files |
| `scripts/bandsheet_verification_report.py` | Fetch public Google Calendar iCal + published Band Sheet JSON, normalize future gigs, and block on mismatches | Booking Phase / Accuracy Check |
| `scripts/website_verification_report.py` | Fetch published Band Sheet JSON + WordPress public show posts, normalize future public shows, and block on public website drift | Website / Accuracy Check |
| `scripts/agentmail_health_check.py` | Verify AgentMail key, inbox visibility, and optional explicit send test without exposing secrets | Email / Health Check |
| `scripts/agentmail_send.py` | Run AgentMail health check, send a Neon V2 operational email, return a safe receipt, and emit a Gmail draft fallback payload when requested | Email / Protected Send |
| `scripts/create_venue_package.sh` | Existing venue package/flyer asset helper | Booking Phase / Promo |
| `scripts/find_rehearsal_dates.py` | Find candidate rehearsal dates | Booking Ops |
| `scripts/check-freshground-calendar.py` | Check Freshground calendar availability | Booking Ops |
| `scripts/monitor_inbox.py` | Flag booking-related inbox messages and, with `--write-intake-receipts`, create local Intake receipts without sending replies | Intake / Email |
| `scripts/neon_monitor.py` | Stub pointing to canonical Hermes monitor | Briefing / Monitoring |
| `scripts/post_gig_payout_tool.py` | Calculate payout totals, track base pay still owed separately from tips, and upsert supervised CSV ledger rows by gig ID | Post-Gig Phase |
| `scripts/post_gig_queue_sync.py` | Sync calendar gigs into a local queue, keep future shows dormant, and activate closeout only after each show ends | Post-Gig Phase |
| `scripts/neon_health_check.py` | Run read-only AgentMail, Band Sheet/calendar, website/Band Sheet, and dashboard-data checks with isolated lane receipts | Cross-phase Verification |
| `scripts/agent_compatibility_check.py` | Verify Codex, Claude, and Hermes share skill access, runtime capabilities, credential availability, and Club Babaloo safety boundaries | Agent Platform |

## Workflow Phases

| Phase | Trigger | AI Work | Script Work | Human Approval |
|---|---|---|---|---|
| Intake Phase | Booking email arrives | Parse request, draft/auto-ack known contacts, create task/reminder | Future intake parser, email monitor | Calendar confirmation |
| Booking Phase | Calendar event exists | Venue Agent reasoning, logistics warnings, mismatch explanation | Venue planner, Band Sheet compare, Scout validator | Publish/send/share/change terms |
| Post-Gig Phase | Show date passes | Ask for pay/tips, summarize missing closeout data, rebooking prompt | Local payout spreadsheet updater | Payment status completion |

## Current Automation

Current working pieces:

- Local test suite for core safety rules.
- Venue Agent dry-run planner.
- Intake Phase email parser.
- Intake Phase local receipt writer.
- Inbox monitor can create Intake receipts in supervised mode with `--write-intake-receipts`.
- Scout lead CSV validator.
- Local venue folder sync can create `/Venues/[Venue]/[Venue - YYYY-MM-DD]/` folders from a single event or the public calendar.
- Public Band Sheet vs public Google Calendar verification checker.
- Public website vs Band Sheet verification checker.
- Calendar connector read path.
- AgentMail protocol reference.
- Supervised Post-Gig payout tracker with a local CSV ledger.
- Post-Gig queue sync creates scheduled and active closeout records from the public calendar.

Current partial/broken pieces:

- Local OAuth token at `~/.hermes/neon_oauth_token.json` has previously failed with `invalid_grant`; use connector/public read path or reauth before relying on local OAuth.
- Dashboard is specified but not implemented.
- Intake parser, local receipt writer, and inbox monitor receipt mode are implemented; scheduled unattended inbox automation is not installed yet.
- Post-Gig payout tracker and automatic queue population are implemented; dashboard form integration is not implemented.
- WordPress API auth has been proven with Application Passwords when a normal User-Agent is supplied. The target for public website cards is `wp/v2/show`, not the full Band Sheet and not the Events Calendar endpoint.

## Deployment Blockers

Supervised deployment is allowed now.

Before unattended production automation:

- Install a scheduled supervised monitor run once Mike approves cadence and receipt folder location.
- Scheduled local venue folder sync is active hourly. It uses `--use-local-model`, but only for missing digest files; existing local notes are left alone.
- Keep unknown-contact acknowledgments draft-only until Mike approves the sender policy.
- Reauth or replace the local OAuth calendar token before relying on local Calendar API automation.
- Build the dashboard approval queue before enabling routine write actions.
- Connect the Post-Gig queue and payout tracker to the dashboard entry form.
- Add a scheduled health check for AgentMail, Band Sheet/calendar alignment, and website/Band Sheet alignment.

## Approval Policy

Known-contact acknowledgment emails may be automated once the Intake Phase tool exists and Mike approves the behavior.

Unknown-contact replies must be drafted for Mike approval.

Calendar entries remain Mike-approved until a later explicit approval flow is designed.

## Experimental Local Model Policy

The local model starts with read-only tasks only:

- Venue folder digest
- Missing-field summary
- Suggested questions for Mike
- Low-risk classification

Current pilot:

- Model server: local llama.cpp on `127.0.0.1:8080`
- Model: `gemma-4-E4B-it-Q4_1.gguf`
- Use `/completion` for digest tasks. The chat endpoint can spend output in `reasoning_content`, which makes normal `content` appear blank in scripts.
- First fixture: `/Volumes/VADER/Manifold/Neon_Blonde/Venues/_Test Venues/Club Babaloo/gigs/2026-10-07/LOCAL_MODEL_DIGEST.md`

It must not:

- Edit calendar
- Publish Band Sheet
- Send email
- Update payment status
- Share portal files
- Modify reconciliation receipts

## Ownership

Mike owns final booking decisions and source-of-truth approvals.

Codex owns Neon V2 system design and orchestration with Mike.

Neon V2 owns routing, reminders, receipts, warnings, and structured handoffs.

Scripts own deterministic validation and local report generation.
