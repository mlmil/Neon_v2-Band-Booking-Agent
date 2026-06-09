# Neon V2 Dashboard Read-Only Slice

Goal: show one screen with current operational state without writing to calendar, Band Sheet, email, portal, or payment records.

Sections:

- Intake queue
- Next gig
- Blocked lanes
- Needs review
- Band Sheet verification status
- Venue Agent queue
- Scout Agent queue
- Post-Gig queue
- Payment/admin queue
- Local model digest

Allowed data sources:

- Live Band Sheet JSON
- Local Venue folders
- Local Scout Agent CSV
- Local Intake Phase tasks
- Local reconciliation receipts
- Local failure receipts
- Future Post-Gig placeholders created from confirmed gigs

Intake read-only view:

- Show booking requests with `needs_calendar_review`.
- Show requester, venue, requested date, start time, source email, and next step.
- Show whether the acknowledgment was auto-sent or needs approval.
- Do not create calendar events from the read-only slice.

Post-Gig read-only view:

- Show confirmed gigs that have passed and need pay/tip entry.
- Show future confirmed gigs as quiet placeholders.
- Surface missing fields: pay received, base pay, tips, method, received by, still owed.
- Do not mark payment complete from the read-only slice.

Protected writes:

- No Google Calendar updates
- No Band Sheet publish
- No email send
- No portal sharing
- No payment completion
