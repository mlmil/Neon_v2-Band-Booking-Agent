---
name: telegram-operations-monitoring
description: Reliable scheduled monitoring of an allowlisted Telegram operations group with checkpointing, first-run backlog suppression, triage, and source-of-truth conflict alerts.
---

# Telegram Operations Monitoring

Use for scheduled or recurring scans of an authorized operations chat, especially when messages must be compared with a published schedule or other binding source of truth.

## Workflow

1. Resolve the allowlisted chat ID and the private state directory before reading messages.
2. Load the checkpoint, if present. The checkpoint must contain a UTC initialization/scan boundary and enough message identity to avoid replay.
3. **First run:** create the checkpoint at the current UTC time before evaluating the backlog. Do not alert on older messages; return the scheduler's exact silent sentinel when required.
4. **Later runs:** ingest only messages newer than the checkpoint. Prefer message ID plus timestamp, and deduplicate by chat ID/message ID.
5. Classify messages as routine or operational. Ignore routine conversation. Review claims about dates, venues, cities, public show times, arrival/load-in/soundcheck, cancellations, availability, equipment, parking, access, pay, and commitments.
6. Compare operational schedule claims against the live published source of truth. Preserve both sources when they differ.
7. For a real conflict, emit one concise alert naming the Telegram claim and the published value. Explicitly distinguish arrival/load-in from public show time. State that the published source remains the plan until the authorized owner publishes a correction.
8. Keep private/financial/sensitive details out of the group-facing alert. Send only the minimum operational correction needed for members to act safely.
9. Advance the checkpoint after successful ingestion, including silent scans; do not advance it past a failed or partial fetch.

## Safety and Reliability

- Never treat a newer or more confident chat claim as an automatic correction to the binding schedule.
- Ambiguous "be there" or "load in" language is not automatically a show-time conflict; label it as ambiguous unless the message clearly changes the public start time.
- One alert per new fact/conflict; retain an audit record or deduplication key.
- If ingestion fails, report a monitoring coverage gap rather than claiming the scan succeeded.
- Do not send messages or publish corrections unless the governing workflow explicitly grants approval.
