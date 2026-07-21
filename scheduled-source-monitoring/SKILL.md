---
name: scheduled-source-monitoring
description: Verify recurring message or source scans with durable checkpoints, ingestion receipts, deduplication, and honest coverage-gap reporting.
---

# Scheduled Source Monitoring

Use for cron-driven monitoring of an external message stream or operational source when the result may be silent. This is a class-level reliability companion for communication-monitoring workflows.

## Required workflow

1. Resolve the allowlisted source and private state directory.
2. Load the checkpoint. It must contain a UTC initialization/scan boundary and enough identity data to avoid replay (prefer source/chat ID plus message ID and timestamp).
3. On first run, write the initialization boundary before evaluating backlog; suppress older messages and return the scheduler's exact silent sentinel when required.
4. On later runs, ingest only records newer than the checkpoint and deduplicate by source ID plus record/message ID.
5. Produce an ingestion receipt for every scan, including source ID, scan interval, fetch status, fetched count, and newest record identity. An updated checkpoint alone is not evidence of a successful read.
6. Classify routine versus actionable records and compare operational claims to the binding source of truth.
7. For discrepancies, preserve both claims, name both sources, distinguish ambiguous logistics (arrival/load-in) from the public event value, and state that the binding source remains active until an authorized correction is published.
8. Keep private, financial, and sensitive details out of shared alerts.
9. Advance the checkpoint only after complete ingestion and receipt creation. Never advance it past a failed or partial fetch.

## Gateway-backed streams

When a gateway or relay is the reader, verify coverage using persisted inbound-message/session evidence or a direct fetch receipt. Do not infer an empty result from an empty local queue, unchanged logs, or a checkpoint that was merely rewritten. If no receipt can establish coverage for the interval, report a monitoring coverage gap and leave the checkpoint at the last verified boundary.

## Verification checklist

- First-run backlog suppression was applied.
- The scan boundary is UTC and durable.
- Message/record IDs and timestamps are retained for deduplication.
- The fetched interval is explicitly covered by a receipt.
- Silent output is used only after a verified empty/action-free scan.
- Failures are reported as coverage gaps, not as "nothing new."
