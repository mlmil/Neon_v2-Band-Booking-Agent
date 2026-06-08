# Rehearsal-Gig Conflict Cross-Reference

## Problem

Mark's Freshground Sound calendar can contain "Neon Blond" rehearsal events on dates the band already has a confirmed gig. This creates a resource conflict that won't be caught by the normal member-out vs gig cross-reference because rehearsals aren't member-outs — they're a scheduling constraint on the band's time and location availability.

## Real Example (May 2026)

- **June 5, 2026** — Band Sheet shows Harry's Night Club & Beach Bar (Pismo Beach) @ 9pm-midnight (confirmed via sent mail; originally listed as "Leashless" on the stale Band Sheet)
- **June 5, 2026** — Freshground calendar has a "Neon Blond" rehearsal at 7-10pm

The rehearsal ends at 10pm, the gig starts at 9pm, and Pismo Beach is ~2 hours from Ventura. These are incompatible — the rehearsal would need to finish by ~6:30pm at the latest to make the gig. The rehearsal may have been booked by a different band member or for a different purpose.

## Where to Check

This cross-reference belongs in three workflows:

### 1. Morning Check-In / Briefing (Phase 1 step 4 → Phase 4 step 14)

After fetching Freshground events and checking sent mail for each rehearsal's origin:
- For each rehearsal in the next 60 days, check its date against the Band Sheet gig list and calendar gig events
- If a date collision exists, flag it in the rehearsal section of the briefing
- Do **not** silently assume one takes priority — the rehearsal may have been added after the gig was booked and may need Mike to resolve

### 2. Quick Pulse Check

The pulse check skips Freshground sent mail cross-reference unless a rehearsal is found within the 14-day window. If one IS found:
- Cross-reference that rehearsal date against any gigs in the same 14-day window
- Flag any conflict as an advisory in the output

### 3. Find Rehearsal Dates (standalone workflow)

When Mike asks for available rehearsal dates:
- The workflow already cross-references band availability (gigs + member outs) against Mark's availability
- But also check: does Mark's calendar already have a Neon Blond rehearsal on a date you're about to suggest? If so, flag that the slot is already taken

## Detection Pattern

```python
# After fetching both sources:
# band_gigs = [(date, venue), ...] from Band Sheet + calendar
# freshground_rehearsals = [(date, end_hour, summary), ...] from iCal feed

for rehearsal_date, _, summary in freshground_rehearsals:
    for gig_date, venue in band_gigs:
        if rehearsal_date == gig_date:
            flag = f"⚠️ Rehearsal conflict: {summary} on {rehearsal_date}"
            flag += f" overlaps with gig at {venue} — needs Mike's attention"
```

## Wording in Briefing

Use plain-language advisory language, not alarmist:

- ✅ "Mark's calendar also shows a rehearsal on June 5 but that's the same night as Harry's — worth checking which one's right."
- ✅ "There's a Freshground rehearsal on the books for the same night as the Yacht Club gig, might want to sort that out."
- ❌ "CONFLICT DETECTED: Rehearsal at 7pm conflicts with gig at 9pm." (too alarmist — let Mike decide the priority)

## Edge Cases

- **Same-night rehearsal before gig**: If the rehearsal ends before the gig starts but the venues are far apart (e.g., Freshground in Ventura → Pismo Beach), still flag it. The drive time may make it impractical.
- **Late-night rehearsal after gig**: A rehearsal starting after a gig ends is usually fine. Only flag if the overlap is within 2 hours (setup/packup/gear transfer time).
- **Multiple consecutive rehearsals**: Mark's calendar may have 2-3 Neon Blond rehearsals in the same week. Each should be individually checked against the gig list. A single rehearsal on a gig night is a flag; two in the same week on non-gig nights is normal activity.
- **Rehearsal on a member-out date**: If a rehearsal falls on a date a band member is marked out, flag it. The member can't attend rehearsal if they're unavailable.
  - **Real example (May 25, 2026 pulse check)**: Freshground had a Neon Blond rehearsal on Tue May 26 @ 7-10pm. Curtis was marked out May 23-26 (all-day event, end date exclusive). The rehearsal was valid for the rest of the band, but Curtis would miss it. Flagged as an advisory rather than a showstopper — the band can rehearse without one member, but Mike should know who's expected to be there.
