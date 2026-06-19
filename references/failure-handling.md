# Failure Handling

Use this when any Neon V2 workflow partially fails, disagrees across sources, or cannot safely continue.

Core rule:

```text
Fail visibly, isolate the broken lane, and protect source-of-truth writes.
```

## Status Model

Use these states in receipts, dashboard rows, verification reports, and agent handoffs:

```text
success
needs_review
blocked
failed
uncertain
```

## Failure Receipt

Every failed or blocked action should produce a short receipt:

```text
action:
status:
source:
what_changed:
what_did_not_change:
failure_reason:
next_step:
```

## Circuit Breakers

| Failure | Status | Stop | Can Continue |
|---|---|---|---|
| Public calendar unavailable, missing, or malformed | `BLOCKED_CALENDAR` | Venue Agent confirmation, Band Sheet publish | Scout research, read-only Band Sheet check, manual receipt draft |
| Venue name does not resolve | `NEEDS_VENUE_REVIEW` | Band Sheet publish, portal sharing | Create reconciliation receipt, list candidate venue matches |
| Band Sheet mismatch | `BANDSHEET_MISMATCH` | Public accuracy claim, publish/deploy | Venue folder work, mismatch report, draft fix |
| SMS-only confirmation | `UNCONFIRMED_COMMUNICATION` | Mark confirmed, update rate/date/time as truth | Log context, draft email asking for confirmation |
| Folder creation fails | `FOLDER_BLOCKED` | File writes into missing folder | Create local report of intended actions |
| Payment data incomplete | `PAYMENT_INCOMPLETE` | Mark payment complete | Keep gig confirmed, leave admin queue open |
| Scout source incomplete | `SCOUT_SOURCE_INCOMPLETE` | Promote lead to Booking Pipeline | Keep lead `researching`, list missing fields |
| Dashboard write fails | `DASHBOARD_WRITE_FAILED` | Assume write succeeded | Show failed action, keep dashboard read-only |
| Weekday gig passes calendar contract | `WEEKDAY_GIG_REVIEW` | Mark booking fully clean without confirmation | Keep dry-run plan visible, ask for confirmation |
| Early Santa Barbara-area weekday gig | `SB_EARLY_WEEKDAY_LOGISTICS` | Mark logistics clean without review | Keep booking visible, flag Kyle/Dave travel timing |

## Protected Writes

## Calendar Detail Handling

Neon V2 uses the public calendar feed without OAuth. Validate:

- title / summary = venue name
- location = city only
- start = gig start time

If a required field is absent from the public feed, mark the event
`NEEDS_VENUE_REVIEW`. Do not request Calendar OAuth as a fallback.

## Test Venue Rule

`Club Babaloo` and `Club Bobaloo` are test venue aliases.

When either appears as the calendar event title:

- Treat the event as test data.
- Do not create a real active venue alert.
- Do not flag the missing real venue folder as a production failure.
- Route dry-run folder plans under `_Test Venues/Club Babaloo`.

These must stop when the relevant verification lane is blocked, failed, or uncertain:

- Band Sheet publish/deploy
- Venue-facing email send
- Venue portal sharing
- Payment status marked complete
- Booking marked confirmed
- Pay/rate terms changed

## Low-Risk Work That Can Continue

These can continue when clearly marked as local or draft:

- Local `RECONCILIATION.md` draft
- Mismatch report
- Scout research note
- Draft email
- Local model digest
- Dashboard read-only display
- List of proposed next actions

## Example Response

```text
Tony's Pizza gig found.
Calendar: OK
Venue folder: OK
Band Sheet: BLOCKED - city mismatch
Payment: NEEDS REVIEW - pay amount missing
Next step: confirm Band Sheet city before publishing.
```
