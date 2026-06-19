# Authoritative Payout CSV Design

Date: 2026-06-11

## Goal

Create a new authoritative 2026 payout CSV under the Neon Blonde administrative
folder. Seed it with every existing row from the current Numbers payout
workbook, add every current calendar gig, and keep it synchronized when calendar
events are added or updated.

## Authoritative File

```text
/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv
```

The existing Numbers workbook remains unchanged as historical source material.
The existing repo payout CSV is not migrated and is not retained as a second
production ledger.

## CSV Schema

```text
VENUE
CITY
DATE
PAYOUT
TIPS
```

No additional columns are written to the CSV.

## Initial Migration

1. Read all rows from the `Neon Blonde Venues` table in:

   ```text
   /Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/📄-neon-blonde_Payouts 2026.numbers
   ```

2. Preserve its venue, city, date, payout, and tips values.
3. Fetch the current public Neon Blonde calendar.
4. Match calendar gigs to imported rows by date plus normalized venue.
5. Add every unmatched calendar gig with blank payout and tips fields.

## Synchronization

The calendar sync updates the authoritative CSV atomically.

- Rows match by date plus normalized venue.
- New calendar events create new rows immediately.
- Calendar changes update venue, city, and date fields when the existing row can
  be matched unambiguously.
- Existing financial fields are never cleared by calendar synchronization.
- Repeated runs do not create duplicate rows.
- Rows no longer found on the calendar remain unchanged.
- Rows are sorted chronologically by date.

## Dashboard Integration

The dashboard reads and writes the authoritative administrative CSV.

- Calendar synchronization creates upcoming rows.
- Dashboard payout entry fills the payout and tips fields on the existing gig
  row.
- Dashboard payout entry must not create a second row for a synchronized gig.
- Club Babaloo test entries continue to use a separate test ledger.

## Automation

Extend the existing scheduled venue/calendar synchronization lane to run the
payout CSV sync whenever it reads the public calendar.

- The automation remains local.
- Writes are restricted to the new administrative CSV.
- The Numbers workbook is never modified.
- Each run returns a receipt with created, updated, and matched counts.
- A failed sync leaves the previous CSV intact.

## Error Handling

- Malformed Numbers rows are retained where possible and reported for review.
- Invalid calendar events are skipped and reported without stopping valid rows.
- File replacement is atomic.
- Missing administrative directory is a blocker.
- Calendar unavailability blocks synchronization but does not alter the current
  CSV.
- No protected external writes occur.

## Testing

Tests cover:

- Numbers row normalization.
- Currency and blank-value handling.
- Legacy row ID generation.
- Date and normalized-venue matching.
- New calendar row creation.
- Calendar row updates without clearing payout data.
- Duplicate prevention across repeated runs.
- Dashboard update of an existing row.
- Atomic write failure behavior.
- Club Babaloo test-ledger isolation.

## Acceptance Criteria

- The new CSV contains every row from the current Numbers payout table.
- It contains every currently valid 2026 calendar gig.
- Existing payout and tip values are preserved.
- Future calendar gigs have blank financial fields.
- The CSV contains only `VENUE`, `CITY`, `DATE`, `PAYOUT`, and `TIPS`.
- Running synchronization twice creates no duplicates.
- Dashboard payout entry updates the matching row.
- Scheduled automation keeps the file current.
- The original Numbers workbook remains unchanged.
