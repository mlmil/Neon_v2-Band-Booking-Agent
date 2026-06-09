# Neon V2 Brainstorm TODO

Date: 2026-06-08

## Resume Point

Continue brainstorming from the approved Venue Agent workflow design:

`docs/superpowers/specs/2026-06-08-venue-agent-workflow-design.md`

## Ideas Captured After Spec Commit

### Scout Agent

- Create a separate Scout Agent ecosystem for prospecting new venues.
- Keep Scout Agent separate from active Venue Agents.
- Target regions:
  - Priority 1: Ventura County, Santa Barbara County
  - Priority 2: San Fernando Valley, LA County
  - Priority 3: Central Coast / overflow
- Scout signals:
  - public venue calendars
  - venue social posts
  - local band social posts
  - local event listings
  - similar-band bookings
- Add band adjacency tracking: if similar bands play a venue, score it as a stronger Neon Blonde lead.
- Add weekly Scout Agent report:
  - top 10 new leads
  - 3 best venues to contact first
  - similar bands/venues discovered
  - dead ends
  - follow-ups due
  - why each lead is worth pursuing

### Scout Agent Ecosystem

Proposed folder:

```text
/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/
  SCOUT_AGENT.md
  scout-leads.csv
  do-not-contact.csv
  regions/
  sources/
  leads/
```

Lead statuses to consider:

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

### Booking Pipeline Agent

Open question: should this be its own subagent or part of Scout Agent?

Proposed purpose:

- bridge the gap between Scout Agent and Venue Agent
- track qualified leads after discovery
- manage outreach status
- draft first-contact emails
- remind Mike/Alfred when follow-up is due
- record replies
- flag when a lead should graduate into an active Venue Agent
- track lead owner: Mike, Alfred, Curtis, or unassigned

Possible statuses:

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

### Neon V2 Dashboard

Approved direction: **Operations Command Center**.

Dashboard should show:

- top priority / next gig
- today's first move
- approvals
- mismatches
- venue follow-ups
- Venue Agent queue
- Scout Agent queue
- Band Sheet verification gate
- money/admin queue
- promo backlog
- local model digest

Dashboard should support basic write actions.

Allowed dashboard writes:

- create/check gig folder
- create `RECONCILIATION.md`
- mark receipt reviewed
- mark payment status: `unpaid`, `paid`, `partial`, `needs review`
- mark flyer status
- draft email
- run Band Sheet verification
- create Scout lead record
- mark lead status

Protected actions needing confirmation:

- send email
- publish Band Sheet changes
- update Google Calendar
- expose/share portal files with venue
- mark a booking fully confirmed
- change pay/rate terms

Design rule:

```text
The dashboard should not be another place to manage everything manually.
It should show what changed, what is blocked, and what needs Mike's decision.
```

### Private Band Contacts

Private contact directory created outside repo:

`/Volumes/VADER/Manifold/Neon_Blonde/Administrative/private-band-member-contacts.md`

Roster/role updates made in:

`references/band-members.md`

Rules:

- Mike Miller and Alfred Morlaes are the primary booking leads for nearly all Neon Blonde venue work.
- Curtis Clyde may occasionally take the lead, but do not assume that unless Mike says so or a thread/source clearly shows Curtis leading that booking.
- Do not copy phone numbers into GitHub-tracked files, public Band Sheet content, venue portal materials, or venue-facing messages unless Mike explicitly asks for a specific number to be shared.

## Next Session

1. Wire `scripts/monitor_inbox.py` to create Intake receipts from flagged booking emails.
2. Keep first deployment in supervised mode: local receipts and drafts are allowed; calendar, Band Sheet, WordPress, payment, portal, and venue-facing email sends still need approval.
3. Build the dashboard approval queue around Intake receipts, mismatch reports, venue-agent receipts, and post-gig payment items.
4. Implement Post-Gig payout entry form and spreadsheet updater.
5. Reauth or replace the local OAuth calendar token before relying on unattended Calendar API automation.
6. Booking Pipeline folder decision: wait until the first qualified Scout leads exist.
7. Later: convert the approved design into a production automation plan.

## Deployment Status

Current status:

```text
Deployable as supervised Neon V2 baseline.
Not ready for unattended production automation.
```

Working supervised pieces:

- Intake email parser.
- Intake local receipt writer.
- Venue Agent dry-run planner.
- Scout CSV validator.
- Band Sheet vs public Google Calendar verification checker.
- Website vs Band Sheet verification checker.
- AgentMail health/send wrapper with Gmail-draft fallback payload.

Remaining production blockers:

- Live inbox monitor does not create Intake receipts yet.
- Dashboard is not implemented.
- Post-Gig payout tracker is not implemented.
- Local OAuth calendar token has known `invalid_grant` history.
- Scheduled live health checks are not installed yet.
