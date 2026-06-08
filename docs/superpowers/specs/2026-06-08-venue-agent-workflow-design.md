# Venue Agent Workflow Design

Date: 2026-06-08
Repo: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2`

## Purpose

Neon V2 remains the main Neon Blonde operations agent. When a committed gig is added to the Neon Blonde calendar, Neon V2 starts a venue-specific workflow that keeps the Band Sheet, venue folders, gig receipts, payout tracking, communication follow-up, and public-facing venue materials aligned.

The goal is to reduce manual venue administration while keeping calendar and Band Sheet accuracy high enough for band members, families, and venue owners who rely on the public URL.

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

Phase 7: Promo automation

- Schedule and run a separate design session for flyer/promo/social automation.
