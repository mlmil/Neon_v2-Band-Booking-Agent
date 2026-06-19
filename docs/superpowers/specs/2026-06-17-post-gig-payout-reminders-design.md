# Post-Gig Payout Reminders Design

Date: 2026-06-17

## Goal

After a Neon Blonde gig, Mike can text or dictate payout numbers into the Neon Telegram bot. The bot writes directly to the payout CSV and the automation emails Mike and Alfred until every past gig has payout info filled.

## Ledger Columns

- `PAYOUT`: base pay received
- `TIP_JAR`: cash tip jar
- `VENMO`: Venmo tips

Historical rows that only contain `TIPS` are migrated into `TIP_JAR`; `VENMO` stays blank for those rows.

## Reminder Rule

For gigs in the post-gig queue with `needs_closeout`:

- wait 3 hours after show end
- check payout CSV for the matching venue/date
- send an AgentMail reminder if any of `PAYOUT`, `TIP_JAR`, or `VENMO` is blank
- repeat once per day until filled
- `$0.00` counts as filled
- `VENMO` is required only for gigs on or after 2026-06-17; older rows may stay blank

## Telegram Intake

The bot accepts practical dictation such as:

```text
tip jar 200 venmo 100 payout 500
```

The first implementation attaches the entry to the oldest open post-gig closeout item.
