---
name: telegram-monitoring-evidence
description: Establish a strict evidence boundary for recurring Telegram monitoring so only authenticated, post-checkpoint group observations drive triage or conflict alerts.
---

# Telegram Monitoring Evidence

Use this class skill for scheduled or recurring Telegram scans where the output depends on whether genuinely new group messages were observed.

## Evidence boundary

1. Read the scheduler-named governing communications contract directly.
2. Resolve only the explicitly allowlisted group and its private checkpoint.
3. Accept an observation only when it contains the allowlisted chat identity, message identity, message content, and a timestamp newer than the checkpoint.
4. Treat DM records, bot-authored group replies, old archive entries, generic cron output, gateway health, unchanged checkpoints, and empty queues as non-evidence for new inbound group activity.
5. Prefer the dedicated persisted inbound observation receipt/stream. A booking-watcher queue or archive is usable only when each record independently satisfies the identity, content, and post-checkpoint requirements.

## Empty intervals and safety

- An empty interval is normal. If the scheduler specifies an exact sentinel, return exactly `[SILENT]` when no qualifying observation exists.
- Do not broaden the search, inspect unrelated sessions or diagnostics, or fetch Telegram history to compensate for missing persisted observations in a tightly scoped scan.
- Do not turn absence of observations into a coverage-gap warning when the scheduler explicitly says absence is normal.
- Do not advance a checkpoint unless the observation scan itself completed successfully under the governing workflow.

## Operational triage

For each qualifying message, determine whether it makes a concrete claim about gig date, venue, address, show time, arrival/load-in, pay, directions, cancellation, availability, equipment, parking, access, or production. Compare that claim with the live Band Sheet and preserve both sources. Keep show time distinct from arrival, load-in, soundcheck, doors, and curfew; ambiguous logistics are not automatically time conflicts.

If no actionable conflict exists, remain silent. If a conflict exists, issue one concise alert naming both values and state that the Band Sheet remains the plan until Mike publishes a correction. Never silently replace the Band Sheet with a newer group claim.

## Related skills

This overlaps with `scheduled-telegram-conflict-scans` and `telegram-operations-monitoring`; those skills remain the workflow-specific umbrellas, while this skill captures the reusable evidence-boundary and empty-interval discipline.
