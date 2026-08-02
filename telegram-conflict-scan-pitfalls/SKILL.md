---
name: telegram-conflict-scan-pitfalls
description: Known pitfalls for scheduled Telegram conflict scans — missing checkpoints, gateway-only evidence, and cron-provider drift.
---

# Telegram Conflict Scan Pitfalls

Reference document for cron-driven Telegram conflict scans. Encodes operational lessons from repeated scan executions in the Neon V2 profile.

## Missing checkpoint files

The canonical persisted checkpoint path `data/telegram/checkpoint.json` may not exist in every deployment. The cron scheduler tracks its own internal checkpoint state, not a user-visible file. When no persisted receipt files exist and no checkpoint is readable, the correct response is `[SILENT]`. Do not backfill a checkpoint from gateway health, cron output history, or session DB inspection.

## Gateway connectivity vs. new messages

A connected Telegram gateway (visible in `gateway_state.json`) confirms the transport pipe is up, not that new group messages arrived. Never cite a connected gateway as evidence that new inbound observations exist.

## Prior cron output is not evidence

The scheduler's output archive at `<profile>/cron/output/<job_id>/` stores past agent responses, not raw Telegram messages. Do not use these files to reconstruct what the group said.

## Cron provider/model drift

When the global inference config changes (provider or model rotates), unpinned jobs fail with a "config drifted" RuntimeError. This is a scheduler-pinning issue, not a Telegram monitoring issue. Do not conflate a skipped run with a coverage gap.