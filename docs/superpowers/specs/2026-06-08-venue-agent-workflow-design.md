# Venue Agent Workflow Design

Date: 2026-06-08
Repo: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2`

## Purpose

Neon V2 remains the main Neon Blonde operations agent. When a committed gig is added to the Neon Blonde calendar, Neon V2 starts a venue-specific workflow that keeps the Band Sheet, venue folders, gig receipts, payout tracking, communication follow-up, and public-facing venue materials aligned.

The goal is to reduce manual venue administration while keeping calendar and Band Sheet accuracy high enough for band members, families, and venue owners who rely on the public URL.

## Operating Phases

Neon V2 work is organized into three phases:

```text
Intake Phase -> Booking Phase -> Post-Gig Phase
```

Intake Phase:

- Before the calendar event exists.
- Handles booking inquiry emails, availability requests, acknowledgment replies, proposed calendar draft/tasks, and daily reminders.
- Email request is pending intake, not a confirmed gig.
- Known booking contacts can receive an automated Neon V2 acknowledgment. Unknown senders require Mike approval before reply.
- Intake tasks remind Mike daily while `needs_calendar_review`.

Booking Phase:

- Starts when Mike puts the event on the calendar.
- Handles Venue Agent workflow, Band Sheet verification, venue/gig folders, reconciliation receipt, promo, portal, logistics review, and payout expectation.
- Calendar event is the confirmed operational trigger.

Post-Gig Phase:

- Starts after the show happens.
- Handles payment, tips, post-gig dashboard entry, payment spreadsheet row, invoice/payment follow-up, show notes, venue relationship follow-up, rebooking opportunity, and archive.
- A confirmed gig should create a future Post-Gig placeholder that becomes active after the show date/time passes.

Reference: `references/operating-phases.md`.

## Source Of Truth

The Neon Blonde calendar event is the operational trigger.

A committed gig event should contain only these required fields:

- Event title: venue name, such as `Tony's Pizza`
- Location: city only, such as `Ventura`, `Santa Barbara`, or `Pismo Beach`
- Start time: gig start time, such as `7pm`

Do not put full street addresses, `California`, `United States`, or extra prose in the location field. The city-only location is part of the data contract because the Band Sheet and venue workflows depend on predictable calendar input.

When that event appears, Neon V2 starts downstream work:

- Check or update Band Sheet data and the public GitHub Pages URL.
- Resolve the venue against `/Volumes/VADER/Manifold/Neon_Blonde/Venues`.
- Create a venue folder if the venue is new.
- Load or create the venue agent profile.
- Create the date-specific gig folder.
- Create the reconciliation receipt.
- Queue payout, promo, portal, communication, and verification tasks.

The calendar is the internal trigger. The Band Sheet/GitHub Pages URL remains the public source of truth for band members, families, and venue owners.

## Venue Agent Folder Model

Each active venue has a folder under:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Venues
```

Each venue folder contains:

```text
VENUE_AGENT.md
```

`VENUE_AGENT.md` stores stable venue facts:

- Canonical venue name
- Aliases used in calendar, email, Band Sheet, and existing folders
- City
- Contact people
- Email and SMS policy notes
- Typical rate or pay expectations
- Payment method habits
- Load-in, setup, parking, and sound notes
- Flyer and marketing preferences
- Portal/shared-folder rules

Each gig gets a date-specific folder:

```text
Tonys Pizza/
  VENUE_AGENT.md
  gigs/
    2026-06-06/
      RECONCILIATION.md
      payout.md
      contact-history.md
      flyer-drafts/
      portal/
        shared-with-venue/
        private/
```

For an existing venue, Neon V2 loads `VENUE_AGENT.md`, creates or checks the date-specific gig folder, creates or updates `RECONCILIATION.md`, and runs the venue-specific checklist.

For a new venue, Neon V2 creates the venue folder, creates a starter `VENUE_AGENT.md`, creates the gig folder, creates `RECONCILIATION.md`, and asks Mike to review the receipt.

## Reconciliation Receipt

Every calendar-triggered gig gets:

```text
RECONCILIATION.md
```

This is the editable audit receipt for the gig. It records:

- Calendar source fields
- Resolved venue folder and venue profile
- Band Sheet/GitHub status
- City, date, and time confirmation
- Venue contact info
- Expected pay/rate/tips fields
- Payment method and payment status
- Flyer/promo status
- Portal/shared-folder status
- Open questions for Mike

If Mike edits the receipt, Neon V2 treats those edits as the corrected local audit note.

Rules:

- Calendar event remains the trigger.
- Receipt corrections do not silently rewrite the calendar.
- If calendar, receipt, and Band Sheet disagree, Neon V2 flags the mismatch.
- No gig is declared clean until the receipt has no blocking open questions.

## Band Sheet Verification Gate

Band Sheet accuracy gets a two-agent verification gate.

Verifier 1 is Codex:

- Pull Neon Blonde Google Calendar events.
- Pull live Band Sheet JSON from GitHub Pages.
- Normalize both sources to date, start time, venue name, and city.
- Produce a mismatch report.

Verifier 2 is Claude or another independent agent:

- Run the same comparison independently.
- Do not reuse Codex conclusions.
- Produce a separate mismatch report.

Neon V2 compares both reports:

- If both say matched, the Band Sheet is considered verified.
- If either finds a mismatch, the Band Sheet is not verified.
- If the two reports disagree, the result is `UNCERTAIN` and both findings are shown to Mike.

Mismatch types:

- Calendar gig missing from Band Sheet.
- Band Sheet gig missing from calendar.
- Same date with wrong venue.
- Same venue/date with wrong city.
- Same venue/date with wrong start time.
- Duplicate or near-duplicate venue names.
- Suspicious formatting, such as `Fox Wine Co _Topa Topa`.

Never publish or declare the Band Sheet accurate until calendar-vs-Band-Sheet verification passes.

## Communication Policy

SMS is allowed for casual communication. Email is required for operational confirmation.

SMS can be used for:

- Quick questions
- Requests to resend a flyer
- Load-in or arrival questions
- Informal availability questions

Email is required for:

- Confirmed dates
- Date or time changes
- Pay/rate changes
- Cancellations
- Special events
- Deposit, payment, or invoice details

If important information arrives by SMS, Neon V2 may log it as context but must mark it:

```text
unconfirmed until emailed
```

SMS details that affect booking, payment, date, time, cancellation, or special-event scope do not become confirmed operational truth until they are emailed to the Neon Blonde account.

Suggested message to venue owners:

```text
Hey [Name], quick heads up as we get more organized on our end.

Text is totally fine for quick questions, but for booking confirmations, date requests, time changes, payment details, or special events, please email us at neonblondevc@gmail.com.

Email is the fastest way to get us locked in because it triggers our band workflow: calendar, Band Sheet, venue folder, flyer/assets, and follow-up reminders. Texts can get buried in personal messages, so we're trying not to use SMS as the source of truth for bookings.

Thanks,
Mike / Neon Blonde
```

## Venue Portal

The Band Sheet should eventually include a visible `Venue Portal` button.

The portal does not expose the whole venue folder. Each venue has a curated shared layer:

```text
portal/
  shared-with-venue/
  private/
```

Venue-facing examples:

- Approved flyer
- Approved promo assets
- Stage plot
- Venmo/payment instructions
- Public band info
- Confirmed gig details

Private/internal examples:

- Payout tracking
- Contact history
- Reconciliation notes
- Internal questions
- Draft notes

The portal can start as a button and routing surface before full login or access-control behavior is implemented. Access control and folder sharing are separate implementation decisions.

## Band Sheet Enhancements

The Band Sheet keeps its current role as the public source-of-truth URL.

Enhancements:

1. Add a booking-season banner above or near `Next Gig`.
2. Add a `Venue Portal` button.
3. Keep desktop and phone visual checks in the release process.
4. Prevent silent drift between deployed public data and local repo data.
5. Enforce the calendar input contract: venue title, city-only location, start time.

Booking-season banner examples:

```text
NOW BOOKING: FALL 2026
NOW BOOKING: WINTER 2027
NOW BOOKING: SPRING 2027
```

The banner should rotate automatically by date. A manual campaign override, such as holiday parties, belongs in the Band Sheet enhancement phase.

Band Sheet verification notes from 2026-06-08:

- Live URL: `https://mlmil.github.io/NeonBlonde-Bandsheet/docs/`
- Live data was current: `June 07, 2026 @ 4:46 PM PT`
- Local `docs/bandsheet-data.json` in `/Volumes/VADER/Manifold/Neon_Blonde/Repos/NeonBlonde-Bandsheet` was stale: `May 24, 2026 @ 5:05 AM PT`
- Live page was usable on desktop and phone, with minor internal header/footer overflow warnings.
- Local uncommitted redesign aligned cleaner on desktop and phone, but used stale local data.

## Promo Automation Backlog

Promo/flyer automation is a major pain point and should be handled in a separate working session.

Problem:

- Flyers are currently made manually.
- Each flyer can take about an hour.
- Uploading to socials adds more manual time.

Backlog item:

- Schedule a dedicated promo/flyer automation design session as a separate calendar item.
- Scope flyer creation, approval, export sizes, venue-specific templates, social posting, and asset handoff separately from the venue-agent workflow.

## Scout Agent

Scout Agent is a separate prospecting ecosystem. It discovers possible new venues before they become active Neon Blonde venues.

Scout Agent does not own confirmed gigs. Once a venue has a committed calendar event, the work moves to the Venue Agent workflow.

Initial target regions:

- Priority 1: Ventura County and Santa Barbara County
- Priority 2: San Fernando Valley and LA County
- Priority 3: Central Coast / overflow

Scout signals:

- Public venue calendars
- Venue social posts
- Local band social posts
- Local event listings
- Similar-band bookings

Band adjacency is a scoring signal. If similar bands are playing a venue, that venue is more likely to be a strong Neon Blonde lead.

Proposed Scout Agent folder:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/
  SCOUT_AGENT.md
  scout-leads.csv
  do-not-contact.csv
  regions/
  sources/
  leads/
```

Created starter files:

- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/SCOUT_AGENT.md`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/scout-leads.csv`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/do-not-contact.csv`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/regions/ventura-county.md`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/regions/santa-barbara-county.md`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/regions/la-valley.md`
- `/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/regions/central-coast.md`

Lead statuses:

```text
discovered
researching
qualified
ready_to_contact
contacted
follow_up
warm
not_a_fit
booked
converted_to_venue_agent
```

Weekly Scout Agent report:

- Top 10 new leads
- 3 best venues to contact first
- Similar bands and venues discovered
- Dead ends
- Follow-ups due
- Why each lead is worth pursuing

Safety rules:

- Use public sources only.
- Do not bypass login walls, private groups, or platform access controls.
- Do not auto-send outreach.
- Do not add a venue to the active Venue Agent folder tree until a gig is actually committed or Mike explicitly promotes the venue.

## Booking Pipeline Agent

Booking Pipeline is the bridge between Scout Agent and Venue Agent.

Decision for initial design: treat Booking Pipeline as its own lane, but not necessarily its own autonomous process yet. This gives the workflow a clear owner for follow-up without adding another heavy automation too early.

Folder decision: do not create a separate Booking Pipeline folder until the first qualified Scout leads exist. Start with the lane definition and statuses, then create the folder around real outreach records.

Booking Pipeline owns qualified leads after discovery:

- Manage outreach status.
- Draft first-contact emails.
- Remind Mike or Alfred when follow-up is due.
- Record replies.
- Track lead owner: Mike, Alfred, Curtis, or unassigned.
- Flag when a lead should graduate into an active Venue Agent.

Pipeline statuses:

```text
qualified
ready_to_contact
draft_needs_review
contacted
waiting_reply
follow_up_due
negotiating
date_offered
booked
not_a_fit
dead
converted_to_venue_agent
```

Graduation rule:

- Scout Agent discovers and researches.
- Booking Pipeline qualifies, drafts, follows up, and negotiates.
- Venue Agent starts only after a committed calendar event or explicit Mike approval.

No pipeline item can be marked `booked` unless the calendar event exists or Mike explicitly says the booking is confirmed.

## Neon V2 Dashboard

Approved direction: Operations Command Center.

The dashboard should show what changed, what is blocked, and what needs Mike's decision. It should not become another manual management surface.

Core dashboard sections:

- Top priority / next gig
- Today's first move
- Approvals
- Mismatches
- Venue follow-ups
- Venue Agent queue
- Scout Agent queue
- Band Sheet verification gate
- Money/admin queue
- Promo backlog
- Local model digest

Allowed dashboard writes:

- Create or check gig folder.
- Create `RECONCILIATION.md`.
- Mark receipt reviewed.
- Mark payment status: `unpaid`, `paid`, `partial`, or `needs review`.
- Mark flyer status.
- Draft email.
- Run Band Sheet verification.
- Create Scout lead record.
- Mark lead status.

Protected actions requiring explicit confirmation:

- Send email.
- Publish Band Sheet changes.
- Update Google Calendar.
- Expose or share portal files with a venue.
- Mark a booking fully confirmed.
- Change pay or rate terms.

The dashboard can perform basic local writes, but any action that changes an outside source of truth or sends communication needs an approval step.

## Failure Handling

Neon V2 should not behave like one long chain where one failure collapses the whole workflow. Each lane needs its own status and receipt.

Core rule:

```text
Fail visibly, isolate the broken lane, and protect source-of-truth writes.
```

Status model:

```text
success
needs_review
blocked
failed
uncertain
```

Every blocked or failed action should produce:

```text
action:
status:
source:
what_changed:
what_did_not_change:
failure_reason:
next_step:
```

Protected writes stop when their verification lane is blocked, failed, or uncertain:

- Google Calendar updates
- Band Sheet publish/deploy
- Venue-facing email send
- Venue portal sharing
- Payment status marked complete
- Booking marked confirmed
- Pay/rate terms changed

Calendar detail fallback:

- If a calendar list response shows an event but omits location/city, fetch the individual event before blocking.
- Do not treat a missing field in the list response as final truth.
- Example: `Ms Special ` on August 15, 2026 has detail location `Goleta`, so it passes the three-field calendar contract.

Low-risk work can continue when clearly marked as local or draft:

- Local `RECONCILIATION.md` draft
- Mismatch report
- Scout research note
- Draft email
- Local model digest
- Dashboard read-only display
- List of proposed next actions

Reference: `references/failure-handling.md`.

## Local Model Pilot

The local model starts as a safe, read-only observer.

Initial task: Venue Folder Digest.

On a schedule, the local model may:

- Scan one venue folder.
- Summarize new files.
- Identify missing pieces.
- List obvious open questions.
- Write a local-only digest note.

The local model may not:

- Edit calendar events.
- Publish Band Sheet data.
- Send emails or texts.
- Update payout records.
- Change venue shared folders.
- Modify reconciliation receipts directly.

Example output:

```text
LOCAL_MODEL_DIGEST.md
- New files found in Tonys Pizza folder.
- June 6 gig has flyer drafts but no final flyer in portal/shared-with-venue.
- Payment method is still blank.
- Contact person Bruce is mentioned but not confirmed in VENUE_AGENT.md.
```

## Current Venue Folders

As of 2026-06-08, the active venue folder root contains:

- `Fess Parker`
- `Fig Mountain`
- `Fox Wine`
- `Harrys`
- `Harrys NIghtclub`
- `Leashless`
- `Ms special`
- `Santa Barabra Yacht Club`
- `The Cruisery`
- `The Garage`
- `The Sewer`
- `Tonys Pizza`
- `Validation Ale`

The implementation needs alias handling because existing folder names may not exactly match calendar or Band Sheet names.

## Implementation Phases

Phase 1: Venue agent profile and receipt structure

- Define `VENUE_AGENT.md` template.
- Define `RECONCILIATION.md` template.
- Add Neon V2 instructions for existing vs new venue handling.
- Add alias-resolution rules.

Phase 2: Calendar-triggered workflow

- Add or update helper script/checklist that turns a calendar event into venue-agent actions.
- Create or check venue folder.
- Create date-specific gig folder.
- Create reconciliation receipt.

Phase 3: Band Sheet verification gate

- Build deterministic calendar-vs-Band-Sheet comparison.
- Define second-agent verification handoff.
- Add mismatch report format.

Phase 4: Band Sheet public enhancements

- Add booking-season banner.
- Add Venue Portal button.
- Add layout checks for desktop and phone.
- Add local-vs-live data drift check.

Phase 5: Portal/shared folder model

- Define `portal/shared-with-venue/` and `portal/private/` expectations.
- Decide access-control mechanism.
- Add venue-facing content rules.

Phase 6: Local model pilot

- Create read-only Venue Folder Digest task.
- Write digest output to local-only files.
- Keep local model out of source-of-truth writes.

Phase 7: Scout Agent and Booking Pipeline

- Create Scout Agent folder ecosystem. Status: starter structure created.
- Define lead CSV schema.
- Define do-not-contact handling.
- Define weekly Scout report format.
- Define Booking Pipeline status model.
- Define lead-to-venue graduation rules.
- Defer separate Booking Pipeline folder until first qualified leads exist.

Phase 8: Neon V2 Dashboard

- Define dashboard data sources.
- Implement read-only overview first.
- Add allowed local write actions.
- Add protected-action approval gates.

Phase 9: Promo automation

- Schedule and run a separate design session for flyer/promo/social automation.
