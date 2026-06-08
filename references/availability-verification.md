# Availability Verification Protocol

## Purpose

Availability checks must be conservative. The goal is to avoid false clears that create booking conflicts.

## Primary Checker

The primary checker reads:
- The Neon Blonde 2026 calendar
- Member unavailability
- Existing gigs on the target date
- Same-day travel and setup constraints

It produces one of three outcomes:
- `CLEAR`
- `CONFLICT`
- `UNCERTAIN`

## Verifier

The verifier repeats the same check independently and compares the answer to the primary checker.

If the verifier differs from the primary checker:
- Do not issue a clear answer
- Report the mismatch
- Ask for a manual follow-up or a narrower date/time window

## Decision Rules

Mark `CLEAR` only when all are true:
- No gig is already booked on that date
- No member is out on that date
- No travel/setup issue creates a practical conflict
- The verifier agrees

Also verify the calendar math:
- Weekday label matches the date
- Month and day are not swapped
- Year is explicit when the date could be ambiguous

Mark `CONFLICT` when any hard conflict exists.

Mark `UNCERTAIN` when:
- The date range is ambiguous
- A member out spans partial days and the calendar context is incomplete
- A travel/setup edge case needs manual review
- The verifier and primary checker disagree

## Overnight Booking Rule

If a gig starts on one date and ends after midnight:
- treat it as one booking on the start date
- do not create a second availability block on the next date just because the end time is `1am` or similar
- only block the next day if there is a separate event or a real overlap on the calendar

Example:
- `SAT SEPTEMBER 14 @ 8pm - 1am` blocks Saturday night, not a separate Sunday booking
- Sunday is only blocked if there is another event or a true next-day conflict

## Recommended Response Format

`Looks clear for Saturday, March 15, but I re-checked it and one thing needs a human pass before I'd call it locked.`

`Tony’s out that weekend, so that one’s a no-go.`

`I'm getting a mismatch on the read, so I'd treat this as uncertain until I verify the exact time window.`

## Overnight Response Format

When a gig runs past midnight, split the answer into the event night and the next day:

`Saturday night is booked until 1am.`

`Sunday is still free unless there is another event.`

Do not imply a second-day booking unless the calendar contains a separate event on that date.

## Timing Definitions

- **Gig night**: The calendar date the event starts
- **Next-day spillover**: Time after midnight that belongs to the same gig night
- **True next-day conflict**: A separate event, rehearsal, travel block, or member-out that begins on the next calendar date

Availability checks must use these definitions:
- If the event starts before midnight and ends after midnight, block the gig night only
- If the next calendar day has no separate event, treat it as open
- If there is a separate booking on the next day, treat that as a real conflict

## Calendar Entry Convention

When reading Neon Blonde calendar events:
- title = venue name
- location field = venue name or venue details
- time field = the actual event time range

Use the title and location together to confirm the venue. Do not create a second date from a late end time in the time field.

## Time Plausibility Checks

Flag these for manual confirmation:
- missing start time
- start time in the AM
- any start time earlier than noon
- Monday through Thursday bookings
- any time that does not match the band's normal play window

Time sanity rule:
- Friday night is normal
- Saturday night is normal
- Sunday afternoon is normal
- anything in the morning is unusual and should be questioned
- weekday gigs are rare enough to require confirmation

Hard gate:
- Do not mark a booking `CLEAR` if it falls outside the normal Friday night / Saturday night / Sunday afternoon window unless a human has explicitly confirmed it.
- Treat unusual timing as `UNCERTAIN` until confirmed.

## Booking Sanity Checklist

Before confirming availability, verify:
- weekday matches the actual date
- the event is one booking night, not a split after midnight
- the time is present and plausible
- the timing fits Friday night, Saturday night, or Sunday afternoon
- weekday or morning bookings have explicit human confirmation

## Decision Tree

1. If the date or weekday is wrong, mark `UNCERTAIN` and fix the date first.
2. If the time is missing or implausible, mark `UNCERTAIN` and ask for confirmation.
3. If the event crosses midnight, keep it on the start date unless there is a separate event.
4. If the time is Friday night, Saturday night, or Sunday afternoon, continue.
5. If it is a weekday or morning booking, mark `UNCERTAIN` unless a human confirmed it.
6. If primary checker and verifier disagree, mark `UNCERTAIN`.
7. Only mark `CLEAR` when everything above passes.

Suggested response:
- `No time is listed, so I need the start time before I can call this clear.`
- `Tuesday gigs are unusual for us. Are you sure this date is right?`
- `That start time looks off, so I'd treat it as uncertain until we verify it.`
