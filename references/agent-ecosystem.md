# Neon V2 Agent Ecosystem

Use this reference when work moves beyond ordinary calendar, Band Sheet, or rehearsal tasks and involves subagents, venue folders, prospecting, dashboard queues, or workflow ownership.

## Agent Map

| Agent / Lane | Owns | Does Not Own |
|---|---|---|
| Neon V2 | Main coordinator, safety checks, calendar/Band Sheet interpretation, routing | Autonomous commitments without Mike approval |
| Venue Agent | Confirmed venue profile, gig folder, reconciliation receipt, payout notes, venue follow-up | Prospecting unconfirmed venues |
| Scout Agent | Prospect discovery, public-source research, lead scoring, weekly lead report | Confirmed gigs, payouts, Band Sheet publishing |
| Booking Pipeline | Qualified leads, outreach drafts, follow-up status, lead owner, graduation to Venue Agent | Public scraping, final booking confirmation |

## Source Of Truth Boundaries

- Calendar event starts confirmed gig workflow.
- Public Band Sheet/GitHub Pages URL is the public source of truth.
- `RECONCILIATION.md` is the editable local audit note.
- Private contacts stay under `$NEON_CONTACTS_ROOT` and never enter public or repository files.
- Scout leads are prospects until promoted by Mike or confirmed through a calendar event.

## Booking Pipeline Decision

Treat Booking Pipeline as its own lane, but not necessarily its own automation at first.

Reason:

- Scout Agent should stay focused on finding leads.
- Venue Agent should stay focused on confirmed venues.
- Follow-up and outreach status is its own operational problem.

This prevents prospecting research from being mixed with active gig administration.

Do not create a separate Booking Pipeline folder until there are qualified Scout leads. Until then, keep the pipeline as a status model and workflow lane.

## Local Write Rules

Allowed local writes:

- Create/check gig folders.
- Create `RECONCILIATION.md`.
- Mark receipt reviewed.
- Mark payment/flyer/lead status.
- Draft email.
- Run verification checks.

Protected actions needing explicit confirmation:

- Send email.
- Publish Band Sheet changes.
- Update Google Calendar.
- Share portal files externally.
- Mark booking fully confirmed.
- Change pay or rate terms.

## Scout Agent Safety

- Use public sources only.
- Do not bypass login walls, private groups, or access controls.
- Do not auto-send outreach.
- Respect `do-not-contact.csv`.
- Keep raw prospect research separate from active venue folders.

## Scout Agent Data

```text
$NEON_DRIVE_ROOT/Scout Agent/
```

Starter files:

- `SCOUT_AGENT.md`
- `scout-leads.csv`
- `do-not-contact.csv`
- `regions/ventura-county.md`
- `regions/santa-barbara-county.md`
- `regions/la-valley.md`
- `regions/central-coast.md`

## Local Tools

- Venue Agent planner: `scripts/venue_agent_tool.py`
- Scout lead validator: `scripts/scout_agent_tool.py`
- Band Sheet verification scaffold: `scripts/bandsheet_verification_report.py`
