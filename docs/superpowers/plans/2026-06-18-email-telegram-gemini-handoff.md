# Email to Telegram Gemini Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Notify Mike in Telegram when a booking email arrives and hand the email into the existing stateful Gemini draft workflow.

**Architecture:** Extend the existing read-only IMAP monitor with a focused notifier. The notifier parses booking context, runs two independent public-calendar checks, persists the active email, and sends one private Telegram alert. Processing state is committed only after notification succeeds.

**Tech Stack:** Python standard library, IMAP, Telegram Bot API, public Google Calendar iCal, unittest.

## Global Constraints

- Never modify Gmail read state or labels.
- Never create, edit, or delete Calendar events.
- Never send venue-facing email without Mike's explicit approval.
- Never expose credentials.
- Failed Telegram delivery must remain retryable.

---

### Task 1: Booking Email Telegram Notifier

**Files:**
- Create: `scripts/booking_email_notifier.py`
- Create: `tests/test_booking_email_notifier.py`

**Interfaces:**
- Consumes: flagged email dictionaries from `scripts.monitor_inbox.build_flagged_email`
- Produces: `notify_booking_email(item: dict) -> dict`

- [ ] Write failing tests for summary extraction, price questions, two-pass calendar results, Telegram delivery, and active-email persistence.
- [ ] Run `python3 -m unittest tests.test_booking_email_notifier` and verify failures are caused by the missing notifier.
- [ ] Implement the minimal notifier with injectable calendar fetch and Telegram request functions.
- [ ] Run `python3 -m unittest tests.test_booking_email_notifier` and verify all tests pass.

### Task 2: Monitor Integration and Retry Boundary

**Files:**
- Modify: `scripts/monitor_inbox.py`
- Modify: `tests/test_monitor_inbox.py`

**Interfaces:**
- Consumes: `notify_booking_email(item: dict) -> dict`
- Produces: processed-message state only after receipt and notification succeed

- [ ] Write failing tests proving notification is invoked and failed delivery does not mark a message processed.
- [ ] Run the focused monitor tests and verify expected failures.
- [ ] Add `--notify-telegram` and integrate notification before processed-ID persistence.
- [ ] Run focused tests and verify they pass.

### Task 3: Gemini Active Email Context

**Files:**
- Modify: `Telegram Bot/telegram_bot/providers/email_context.py`
- Modify: `Telegram Bot/tests/test_gemini_neon_agent.py`

**Interfaces:**
- Consumes: `~/.hermes/neon_active_booking_email.json`
- Produces: `EmailMessage` used by `GeminiNeonAgent`

- [ ] Write a failing test showing persisted active email takes priority.
- [ ] Run the focused test and verify the failure.
- [ ] Add local active-email loading with IMAP fallback.
- [ ] Run the focused tests and verify they pass.

### Task 4: Scheduled Deployment and Verification

**Files:**
- Modify: `scripts/automation/wrapper_gmail_intake.sh`
- Modify: `references/automation-map.md`

- [ ] Enable `--notify-telegram` in the existing scheduled wrapper.
- [ ] Run the full monitor and Telegram bot test suites.
- [ ] Run the compatibility check and Telegram health check.
- [ ] Restart the Gmail intake and Telegram LaunchAgents.
- [ ] Verify both services are loaded and inspect logs for credential-free errors.
