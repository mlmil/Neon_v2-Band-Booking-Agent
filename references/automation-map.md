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
| Codex | Mastermind/orchestration layer for Neon V2 design, architecture, specs, engineering, local scripts, tests, repo edits, and dry-run validation | Design the system with Mike, route work across phases, build/verify tools, read local files, draft specs, run dry-run checks | Source-of-truth writes unless Mike asks |
| Claude | Second-opinion checker, independent review, Band Sheet verification partner | Independently compare calendar/Band Sheet, review plans/specs | Reuse Codex conclusions as its own verification |
| Hermes Agent | Local automation runner / operational bridge | Scheduled checks, reminders, local workflow execution | Silent source-of-truth writes |
| Antigravity | Available AI workspace/model lane | Future specialized work; role not finalized | Production ownership until defined |
| Local model | Experimental observer | Read-only digest, folder summaries, low-risk classification | Calendar, Band Sheet, email, payout, portal, or receipt writes |

Current assignment rule:

```text
Codex is the mastermind. Other agents are assigned specific lanes only after Mike and Codex define the lane clearly.
```

## Deterministic Local Scripts

These scripts should do predictable work and return structured output.

| Script | Purpose | Phase |
|---|---|---|
| `scripts/venue_agent_tool.py` | Validate calendar-shaped event data and produce venue/gig/receipt dry-run plan | Booking Phase |
| `scripts/intake_email_parser.py` | Parse booking-request email text into venue/date/time/city fields, missing-info flags, and an acknowledgment draft without booking anything | Intake Phase |
| `scripts/intake_receipt_tool.py` | Wrap parsed booking-request email text with source metadata and write a local Intake Phase receipt/task | Intake Phase |
| `scripts/scout_agent_tool.py` | Validate Scout Agent lead CSV structure and statuses | Intake / Scout |
| `scripts/bandsheet_verification_report.py` | Fetch public Google Calendar iCal + published Band Sheet JSON, normalize future gigs, and block on mismatches | Booking Phase / Accuracy Check |
| `scripts/website_verification_report.py` | Fetch published Band Sheet JSON + WordPress public show posts, normalize future public shows, and block on public website drift | Website / Accuracy Check |
| `scripts/agentmail_health_check.py` | Verify AgentMail key, inbox visibility, and optional explicit send test without exposing secrets | Email / Health Check |
| `scripts/agentmail_send.py` | Run AgentMail health check, send a Neon V2 operational email, return a safe receipt, and emit a Gmail draft fallback payload when requested | Email / Protected Send |
| `scripts/create_venue_package.sh` | Existing venue package/flyer asset helper | Booking Phase / Promo |
| `scripts/find_rehearsal_dates.py` | Find candidate rehearsal dates | Booking Ops |
| `scripts/check-freshground-calendar.py` | Check Freshground calendar availability | Booking Ops |
| `scripts/monitor_inbox.py` | Existing inbox monitor script | Intake / Email |
| `scripts/neon_monitor.py` | Stub pointing to canonical Hermes monitor | Briefing / Monitoring |

## Workflow Phases

| Phase | Trigger | AI Work | Script Work | Human Approval |
|---|---|---|---|---|
| Intake Phase | Booking email arrives | Parse request, draft/auto-ack known contacts, create task/reminder | Future intake parser, email monitor | Calendar confirmation |
| Booking Phase | Calendar event exists | Venue Agent reasoning, logistics warnings, mismatch explanation | Venue planner, Band Sheet compare, Scout validator | Publish/send/share/change terms |
| Post-Gig Phase | Show date passes | Ask for pay/tips, summarize missing closeout data, rebooking prompt | Future payout spreadsheet updater | Payment status completion |

## Current Automation

Current working pieces:

- Local test suite for core safety rules.
- Venue Agent dry-run planner.
- Intake Phase email parser.
- Intake Phase local receipt writer.
- Scout lead CSV validator.
- Public Band Sheet vs public Google Calendar verification checker.
- Public website vs Band Sheet verification checker.
- Calendar connector read path.
- AgentMail protocol reference.

Current partial/broken pieces:

- Local OAuth token at `~/.hermes/neon_oauth_token.json` has previously failed with `invalid_grant`; use connector/public read path or reauth before relying on local OAuth.
- Dashboard is specified but not implemented.
- Intake parser and local receipt writer are implemented, but the live inbox monitor is not wired to create receipts automatically yet.
- Post-Gig payout spreadsheet updater is specified but not implemented.
- WordPress API auth has been proven with Application Passwords when a normal User-Agent is supplied. The target for public website cards is `wp/v2/show`, not the full Band Sheet and not the Events Calendar endpoint.

## Deployment Blockers

Supervised deployment is allowed now.

Before unattended production automation:

- Wire `scripts/monitor_inbox.py` to create Intake receipts from flagged booking emails.
- Keep unknown-contact acknowledgments draft-only until Mike approves the sender policy.
- Reauth or replace the local OAuth calendar token before relying on local Calendar API automation.
- Build the dashboard approval queue before enabling routine write actions.
- Implement Post-Gig payout spreadsheet updates and dashboard entry form.
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
