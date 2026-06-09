# Neon V2 Operating Phases

Use this when routing Neon Blonde work across email intake, confirmed gig operations, and post-show closeout.

## Phase Model

```text
Intake Phase -> Booking Phase -> Post-Gig Phase
```

## Intake Phase

Before the calendar event exists.

Owns:

- Booking inquiry emails
- Availability requests
- AI acknowledgment replies
- Extracted venue/date/time/city/requester fields
- Proposed calendar draft/task
- Daily reminders until Mike resolves the request

Status examples:

```text
requested
needs_calendar_review
waiting_on_mike
waiting_on_requester
declined
converted_to_calendar
```

Rule:

```text
Email request = pending intake, not a confirmed gig.
```

Parser:

```bash
python3 scripts/intake_email_parser.py --text "Can we book M Special on August 15 at 7pm in Goleta?"
```

The parser returns a receipt with:

- `status`: `ready_for_mike_review` or `needs_info`
- `venue`
- `date`
- `time`
- `city`
- `missing_fields`
- `review_flags`
- `acknowledgment_draft`

Relative dates such as `next Saturday` must stay in `needs_info` with `RELATIVE_DATE_REVIEW`. Do not convert them without checking the source email date.

Local receipt writer:

```bash
python3 scripts/intake_receipt_tool.py \
  --sender "booking@example.com" \
  --subject "M Special August date" \
  --source-date "Tue, 09 Jun 2026 10:00:00 -0700" \
  --text "Can we book M Special on August 15 at 7pm in Goleta?"
```

Default output:

```text
data/intake/receipts/
```

Stopping-point rule:

```text
Intake receipt written = local task exists. No calendar update, Band Sheet update, or email send has happened yet.
```

## Intake Task Format

Every booking request email should produce an Intake Phase task:

```text
status:
requester_name:
requester_email:
source_email_subject:
source_email_date:
source_email_link:
venue:
city:
requested_date:
start_time:
special_event:
pay_details:
promo_needs:
notes:
next_step:
reminder_due:
calendar_event_id:
```

Required minimum fields:

- requester email
- venue or unresolved venue text
- requested date
- start time, or `unknown`
- source email reference
- status

## Intake Acknowledgment

For known booking contacts, Neon V2 may send an acknowledgment automatically. For unknown senders, draft the acknowledgment for Mike approval.

Preferred acknowledgment:

```text
Hi [Name],

Got it, thanks. This is Neon V2, Neon Blonde's automated booking assistant. We received your request for [Venue] on [Date] at [Time], and we're checking it on our end.

If there are any extra details you want us to know, feel free to send them over:
- whether this is a regular show or special event
- preferred set length
- load-in or sound notes
- pay/rate details
- promo/flyer needs
- anything the venue wants included

No problem if you don't have anything else right now. Mike will review the date and I'll follow up and confirm with you once everything's checked.

- Neon V2
Neon Blonde Booking Assistant
```

## Intake Reminder Rules

```text
needs_calendar_review -> remind Mike daily
waiting_on_requester -> do not nag Mike daily unless the requested date is within 14 days
converted_to_calendar -> stop intake reminders and start Booking Phase
declined -> close intake
```

If an Intake Phase request sits unresolved for more than 48 hours, surface it in the dashboard and daily brief as `needs_calendar_review`.

## Booking Phase

After Mike puts the event on the calendar and before the show happens.

Owns:

- Venue Agent workflow
- Band Sheet verification
- Venue folder and gig folder
- `RECONCILIATION.md`
- Promo/flyer workflow
- Venue portal/shared assets
- Logistics review
- Payout expectation

Status examples:

```text
calendar_confirmed
bandsheet_pending
venue_folder_ready
promo_pending
logistics_review
contract_pending
signed_contract_received
test_payment_pending
deposit_pending
deposit_received
ready
```

Rule:

```text
Calendar event = confirmed operational trigger.
```

## Contract And Deposit Tracking

For private events, weddings, parties, and any gig with a written agreement, track the contract lane separately from payment.

Do not collapse these states:

```text
contract_sent
signed_contract_received
test_payment_pending
deposit_pending
deposit_received
fully_signed_copy_returned
```

Rules:

- A signed attachment or signed Drive doc means `signed_contract_received`, not `deposit_received`.
- A $1 Venmo/Zelle/check test proves the payment path, not the deposit.
- A booking is not locked for accounting until the actual deposit amount is confirmed received.
- If the signed contract and email thread disagree on performance time, use `TIME_MISMATCH_REVIEW` and keep the final-copy return blocked until Mike resolves the time.
- Once deposit is received, next follow-up is returning the fully signed copy unless that has already happened.

Use `scripts/contract_flow.py` when converting email/Drive evidence into dashboard or briefing states.

## Post-Gig Phase

After the show happens.

Owns:

- Payment received
- Tips logged
- Payout/tip dashboard entry
- Post-gig payment spreadsheet row
- Invoice/payment follow-up
- Show notes
- Venue relationship follow-up
- Rebooking opportunity
- Final archive

Status examples:

```text
payment_pending
tips_pending
partial_payment
paid_complete
followup_needed
rebook_opportunity
closed
```

Rule:

```text
Show date passed = closeout starts.
```

## Post-Gig Payment Tracking

When a gig is confirmed in the Booking Phase, create a future Post-Gig dashboard item. Keep it quiet until the show date/time passes.

After the gig passes, move the item into the active Post-Gig queue and ask Mike for:

- Pay received: yes / no / partial
- Base pay amount
- Tips amount
- Payment method: cash / check / Venmo / Zelle / other
- Received by
- Still owed
- Notes

Dashboard form fields:

```text
venue
date
pay_received
base_pay_amount
tips_amount
payment_method
received_by
still_owed
notes
```

Payment spreadsheet fields:

```text
gig_id
venue
city
date
base_pay_expected
base_pay_received
tips_received
total_received
payment_method
received_by
still_owed
payment_status
entered_by
entered_at
notes
```

The agent should keep reminding Mike until payment and tips are recorded or explicitly marked unknown.

## Phase Boundaries

- Calendar event appears: Intake Phase ends, Booking Phase starts.
- Show date/time passes: Booking Phase ends, Post-Gig Phase starts.
- If a post-gig payment issue reopens, keep the gig in Post-Gig Phase until money/admin is closed.
