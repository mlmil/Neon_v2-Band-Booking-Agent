# Briefing Cross-Reference

Use this during morning briefings and pulse checks after fetching calendar, Band Sheet, email, Freshground, and pending approval data.

## Cross-Reference Order

1. Check each Band Sheet gig against member-out events on the Neon Blonde calendar.
2. Expand member-out ranges from calendar `start` and `end`; the Band Sheet can truncate multi-day end dates by one day.
3. Escalate any tentative member-out (`probably`, `maybe`, `tentative`) that overlaps a confirmed gig.
4. Compare booking-contact emails against Band Sheet dates and times.
5. Compare Band Sheet gigs against calendar events.
6. Compare calendar gig-like events against Band Sheet listings.
7. Check venue folders for each near-term confirmed gig.
8. Check sent mail when venue names, dates, or times disagree.
9. Cross-reference Freshground rehearsals against sent rehearsal requests and confirmed gigs.

## Compounding Signal Assessment

Rate each upcoming gig with these signals:

| Signal | Negative means |
|---|---|
| Band Sheet freshness | Updated date is more than 4 days old |
| Calendar match | No matching event by date and venue |
| Venue folder | No matching folder for venue and date |
| Email consistency | Incoming email says a different date or time |
| Sent mail trail | No sent confirmation or resolution found |
| Tentative member-out | A maybe/probably out overlaps the gig |

Treatment:
- `0 negatives`: present as solid.
- `1 negative`: advisory.
- `2+ negatives`: elevated uncertainty; needs Mike's attention.
- `1+ negative plus tentative member-out overlap`: highest priority item.

## Venue Folder Rules

Venue folders may use either `Venue Name - YYYY-MM-DD` or `Venue Name - M D YYYY`. Search by venue and date rather than assuming one exact format.

Filter out folders that are actually member-out records, such as `Kyle Out - 7 3 2026`.

Do not create missing venue folders during a briefing unless Mike asks. Flag them as action items.

## Sent Mail Resolution

When Band Sheet and calendar disagree, search sent mail before asking Mike.

Use subject searches first because Mike often names the venue in the subject. Fall back to body search only when subjects are silent.

Negative sent mail searches are meaningful. If the Band Sheet is stale, no calendar event exists, and no sent mail confirms the date, keep the item uncertain.

## Rehearsal Cross-Reference

For Freshground events:
- Convert UTC to Pacific before grouping by day.
- Search sent mail to `freshgroundrecords@gmail.com` for rehearsal or practice subjects.
- Ignore admin emails about DNS, website, calendar setup, or Google Workspace.
- Flag any rehearsal that overlaps a confirmed gig or relevant member-out.
