---
name: telegram-scan-evidence-boundaries
description: Preserve strict evidence boundaries for scheduled Telegram scans by filtering persisted observations against an allowlisted chat and private checkpoint.
---

# Telegram Scan Evidence Boundaries

Use this class skill for recurring, cron-driven Telegram monitoring where an exact silent sentinel is required when no qualifying new inbound group observation exists.

## Procedure

1. Read the scheduler-named governing communications contract directly.
2. Resolve only the explicit allowlisted chat ID and the private checkpoint.
3. Prefer the dedicated persisted observation stream or receipt. In the Neon V2 repository, the private boundary is `data/telegram/checkpoint.json`; persisted archive or booking-watcher records are candidates only, not automatically qualifying observations.
4. Accept a record only when it independently contains:
   - the exact allowlisted chat identity;
   - a message identity;
   - message content; and
   - a timestamp or message position newer than the private checkpoint.
5. When `last_message_id` is null or unchanged, compare the record timestamp with the checkpoint scan boundary. Do not infer newness from file modification, scheduler success, or an unchanged checkpoint.
6. Exclude DMs, other chat IDs, bot-authored group replies, old archive entries, generic cron output, diagnostics, and records missing identity or content.
7. Do not fetch Telegram history, use broad exports, inspect session databases, or broaden the source to manufacture evidence.
8. If no qualifying new inbound group record remains and the scheduler specifies a sentinel, return exactly `[SILENT]`. Empty intervals are normal and are not coverage gaps.

## Conflict triage

For each genuinely new operational claim, compare show date, venue, city/address, show time, arrival, load-in, pay, directions, cancellation, availability, equipment, parking, access, and production facts with the live Band Sheet. Keep show time distinct from arrival, load-in, soundcheck, doors, and curfew; ambiguous logistics are not time conflicts.

If a real actionable conflict exists, issue one concise alert naming both values and state that the Band Sheet remains the plan until Mike publishes a correction. If no conflict exists, remain silent. Preserve deduplication identity and advance the checkpoint only after the observation scan completes successfully.

## Related skills

This overlaps with `scheduled-telegram-conflict-scans`, `telegram-monitoring-evidence`, and `telegram-operations-monitoring`; use the governing scheduled-scan skill when available, and use this skill for the evidence-filtering details above.
