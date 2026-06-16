# Telegram Booking Watcher Design

Date: 2026-06-16
Bot: `NeonBotstein_Bot`
Lane: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot`

## Goal

Add an always-on booking watcher for Neon Blonde Telegram conversations.

The watcher should catch booking-relevant messages that would otherwise disappear
inside band chat, archive them locally, compare them against Neon V2 scheduling
sources, and alert the band when Mike may need to update Google Calendar.

Mike remains the only person who edits Google Calendar.

## Problem Example

Kyle booked a June 27 party months earlier. Later, he mentioned in Telegram that
the June 27 party was canceled. Nobody noticed, so the date stayed on the
calendar and the band lost the chance to book that night.

The watcher exists to prevent that class of failure.

## Authority Model

- Telegram is conversation and evidence.
- Band members can discuss, book, cancel, and correct booking details in
  Telegram.
- Google Calendar is the authoritative schedule, but only Mike can edit it.
- Band Sheet is public operational output and must be checked for mismatches.
- Neon V2 detects conflicts and creates alerts.
- Neon V2 does not edit Google Calendar, publish Band Sheet changes, send venue
  email, update WordPress, or change payment state.

## Scope

V1 should watch the main Neon Blonde Telegram group where booking conversations
happen.

V1 should:

- Archive relevant Telegram messages locally.
- Detect booking-impacting messages.
- Extract structured signals such as date, venue, member, change type, quoted
  text, and confidence.
- Cross-check detected signals against Google Calendar read-only context and the
  Band Sheet.
- Create a local Calendar Attention Queue item for Mike.
- Alert the whole band when the issue is high priority.
- Optionally send Mike a private operator summary when his private chat ID is
  configured.

V1 should not:

- Delete, create, or edit Google Calendar events.
- Publish Band Sheet changes.
- Send venue-facing emails.
- Treat model extraction as final truth.
- Alert on ordinary chatter with no booking impact.
- Require Gig Copilot to run.

## Relationship To Gig Copilot

`GigCopilotNeon_Bot` remains the day-of-show logistics bot.

`NeonBotstein_Bot` owns ongoing booking operations and calendar mismatch
detection.

Gig Copilot may later read the watcher queue and booking history so it knows the
larger context of a show, but it should not be the primary booking watcher.

## Signal Categories

The watcher should detect these booking-impacting categories:

- `cancellation`: canceled, off, not happening, party canceled
- `new_booking`: booked us, got us a gig, they want us, confirmed
- `reschedule`: moved, new date, pushed, changed to another day
- `time_change`: now starts at, load-in changed, earlier, later
- `venue_change`: different venue, new address, moved locations
- `hold_or_tentative`: hold this date, maybe, pencil in, tentative
- `availability_conflict`: I am out, cannot make it, gone that weekend
- `calendar_mismatch`: Telegram says one thing while Calendar or Band Sheet says
  another

## Priority Rules

Immediate band-wide alert:

- cancellation
- reschedule
- confirmed new booking
- time change for a booked gig
- venue/location change for a booked gig
- any extracted signal that conflicts with a currently booked Calendar or Band
  Sheet date

Queue only unless repeated or close to show date:

- tentative holds
- vague booking leads
- member availability comments with no matching booked date

Archive only:

- ordinary logistics chatter
- jokes
- reactions
- messages with no date, venue, booking intent, or availability impact

## Alert Wording

The bot should use cautious language. It should flag possible calendar work, not
declare final truth.

Band-wide example:

```text
NEON CALENDAR FLAG

Kyle mentioned a possible cancellation:
"the party in June 27th is canceled"

June 27 still appears booked.
Mike needs to verify/update the calendar.
Reply here if this is wrong.
```

Mike private example:

```text
Calendar attention needed:

Source: Kyle in Telegram
Message: "the party in June 27th is canceled"
Possible date: June 27
Calendar status: still booked
Band Sheet status: still booked

Suggested action:
Review and update Google Calendar manually.
```

## Local Data

Use local files first. SQLite is preferred once queue state becomes searchable or
needs status transitions.

Suggested V1 paths:

```text
data/telegram/messages/
data/telegram/booking_watcher/queue.jsonl
data/telegram/booking_watcher/archive.jsonl
data/telegram/booking_watcher/reviewed.jsonl
```

Suggested queue fields:

- `id`
- `created_at`
- `source_chat_id`
- `source_message_id`
- `source_sender_name`
- `source_sender_username`
- `message_date`
- `message_text`
- `signal_type`
- `extracted_date`
- `extracted_venue`
- `confidence`
- `calendar_match`
- `bandsheet_match`
- `priority`
- `status`
- `alerted_at`
- `reviewed_at`
- `reviewed_by`

Allowed statuses:

- `open`
- `alerted`
- `reviewed`
- `dismissed`

## Commands

Add or reserve these commands for `NeonBotstein_Bot`:

- `/flags` - show open Calendar Attention Queue items
- `/flag <id>` - show one queue item with evidence and source context
- `/reviewed <id>` - mark an item reviewed after Mike handles it manually
- `/dismiss <id>` - dismiss a false positive
- `/watch-status` - show whether Telegram watcher is configured and active

Commands that mutate queue state should only be accepted from Mike's configured
private chat or a configured admin allowlist.

## Detection Architecture

1. Telegram transport receives group messages.
2. Raw message metadata is archived locally.
3. A rules pre-filter checks for booking, date, cancellation, change, venue, and
   availability keywords.
4. Candidate messages go to a model extractor, with Gemini as the preferred
   provider when available.
5. Extracted signals are normalized into queue candidates.
6. Neon V2 cross-checks candidates against read-only Calendar and Band Sheet
   data.
7. High-priority candidates are posted to the band group and added to the queue.
8. All candidates remain queryable through `/flags`.

Rules should run before the model to reduce noise and cost.

## Error Handling

- If Telegram polling fails, log the failure and leave queue state untouched.
- If model extraction fails, archive the message and create no high-confidence
  alert.
- If Calendar or Band Sheet data is unavailable, create an `open` queue item
  with `calendar_match` or `bandsheet_match` set to `unknown`.
- If the bot cannot post to the band group, keep the item `open` and surface the
  send failure in `/watch-status`.
- If the Band Sheet is stale, include a freshness warning in Mike's private
  summary and queue detail.

## False Positive Strategy

Start aggressive for high-cost failure modes. A false alarm is less expensive
than missing a cancellation or confirmed booking.

The wording must stay careful:

- Say "possible cancellation" instead of "canceled"
- Say "calendar attention needed" instead of "calendar is wrong"
- Include the original quoted Telegram message
- Ask the band to correct the bot if the interpretation is wrong

## Tests

Unit tests should cover:

- Cancellation phrase produces a high-priority candidate.
- Confirmed booking phrase produces a high-priority candidate.
- Vague hold phrase creates queue-only priority.
- Ordinary chatter is archive-only.
- Calendar mismatch raises priority.
- Stale Band Sheet appears as a warning, not a silent pass.
- `/flags` lists open items.
- `/reviewed <id>` changes only local queue status.
- Unauthorized queue mutation is rejected.

Integration smoke tests should cover:

- Telegram update with group message archives raw metadata.
- Candidate extraction creates a queue item.
- High-priority item attempts one band-wide alert.
- No Calendar, Band Sheet, email, WordPress, or payment writes occur.

## Acceptance Criteria

- The bot can archive Telegram group messages without exposing secrets.
- The bot can detect likely booking-impacting messages.
- The bot can create durable Calendar Attention Queue items.
- High-priority issues are surfaced to the band group.
- Mike can list and mark items reviewed.
- Calendar remains Mike-write-only.
- Existing NeonBotstein commands continue to pass tests.

