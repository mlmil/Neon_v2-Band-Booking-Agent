---
name: telegram-operations-monitoring
description: Reliable scheduled monitoring of an allowlisted Telegram operations group with checkpointing, observed-message triage, and Band Sheet conflict alerts.
---

# Telegram Operations Monitoring

Use this class skill for scheduled or recurring scans of an authorized Neon Blonde Telegram operations group when messages must be compared with the published Band Sheet.

## Scheduled Scan Workflow

1. Read the governing communications-triage contract directly.
2. Resolve the explicit allowlisted chat ID and private checkpoint.
3. Inspect only persisted inbound observations for that chat newer than the checkpoint. Do not fetch Telegram history, use a broad chat export, inspect unrelated sessions, or perform setup/environment diagnostics to manufacture evidence.
4. Treat a message as verifiable only when the observation/receipt includes the authorized chat identity, message identity, and content. Prior cron output, gateway health, or an unchanged checkpoint is not a new inbound message.
5. If there is no verifiable new inbound group message, return the scheduler's exact `[SILENT]` sentinel. An empty interval is normal and must never be reported as a coverage gap.
6. Evaluate genuinely new claims about gig date, venue, address, show time, arrival/load-in, pay, directions, cancellation, availability, equipment, parking, access, or production.
7. Compare each relevant claim with the live published Band Sheet. Keep public show time distinct from arrival, load-in, soundcheck, doors, and curfew.
8. If no actionable conflict exists, remain silent. If a real conflict exists, issue one concise alert naming the Telegram value and Band Sheet value, and state that the Band Sheet remains the plan until Mike publishes a correction.
9. Preserve deduplication identity and advance the checkpoint only after the observation scan completes successfully.

## Safety and Reliability

- Never treat a newer or more confident group claim as an automatic correction to the Band Sheet.
- Ambiguous “be there” or “load in” wording is not a show-time conflict unless the message clearly changes the public start time.
- Do not expose private email, contract, home-address, access-code, or payment details in a group alert.
- Do not send messages or publish corrections unless the governing workflow explicitly grants approval.
- Distinguish a successful empty scan from a failed ingestion attempt: only the latter warrants a coverage-gap report.

## References

See `references/communications-triage.md` for the governing triage contract and source-of-truth rules.