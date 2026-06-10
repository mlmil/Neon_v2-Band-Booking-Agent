# Task 002: Dashboard Post-Gig Integration

## Objective

Create the first real Neon V2 dashboard vertical slice. Preserve the exported
dashboard design, but replace its mock Post-Gig Money records and local payout
save action with real data from:

```text
data/post_gig/queue.csv
data/post_gig/payouts.csv
```

This task must not connect or modify the other dashboard panels.

## Required Reading

1. `SKILL.md`
2. `AGENT_COMPATIBILITY.md`
3. `handoffs/antigravity/README.md`
4. `design_handoff_neon_v2_dashboard/README.md`
5. `design_handoff_neon_v2_dashboard/Connection Notes.md`
6. `scripts/post_gig_queue_sync.py`
7. `scripts/post_gig_payout_tool.py`

## Existing Work To Preserve

Do not modify:

- `schemas/scout_leads_schema.json`
- `scripts/scout_agent_tool.py`
- `Neon V2 dashboard.zip`
- `design_handoff_neon_v2_dashboard/`
- any existing credential file
- any unrelated untracked directory

The design handoff is source material. Create the working dashboard separately.

## Architecture

Create:

```text
dashboard/
  index.html
  assets/
  components/
  data/

scripts/dashboard_server.py
tests/test_dashboard_server.py
```

Copy the necessary prototype files into `dashboard/`. Preserve the visual design
and existing confirmation behavior.

Use a Python standard-library localhost server on `127.0.0.1:8787`.

Endpoints:

```text
GET  /api/post-gig
POST /api/post-gig/payout
```

`GET /api/post-gig`:

- Read `data/post_gig/queue.csv`.
- Read `data/post_gig/payouts.csv` when present.
- Merge by `gig_id`.
- Return only queue items where `queue_status` is `needs_closeout` or `closed`.
- Map records into the dashboard's existing `post_gig_items` shape.
- Never expose credential data.

`POST /api/post-gig/payout`:

- Accept a JSON payout form.
- Call the existing functions in `scripts/post_gig_payout_tool.py`.
- Update the real local payout ledger.
- Reject `paid_complete`; this endpoint is only the safe local save action.
- Return a redacted receipt and refreshed Post-Gig item.

Do not shell-interpolate user data. Import and call the existing Python
functions directly.

## TDD Requirements

Write tests first and verify they fail before implementation.

Required tests:

1. Queue and payout rows merge by `gig_id`.
2. A missing payout ledger still returns active queue items.
3. Saved payout defaults Venmo to `@neonblondeband`.
4. Saved payout does not mark payment complete.
5. A request containing `payment_status: paid_complete` is rejected.
6. API responses contain no password/token/API-key fields.
7. Club Babaloo data is clearly marked as test data.

## Frontend Changes

Only change the Post-Gig Money lane:

- On dashboard load, fetch `/api/post-gig`.
- Replace `window.NEON_DATA.post_gig_items` with the response.
- Keep the rest of `window.NEON_DATA` mock data unchanged.
- The payout modal saves through `POST /api/post-gig/payout`.
- After save, refresh the Post-Gig Money lane.
- Show a blocked/error toast if the local server is unavailable.
- Do not add a protected “mark paid complete” API implementation.

## Safe And Protected Boundaries

Allowed:

- Read local queue and payout CSV files.
- Write `data/post_gig/payouts.csv` through the existing payout tool.
- Serve dashboard files locally.
- Write tests.

Not approved:

- Calendar writes
- Email sends
- Band Sheet publishing
- WordPress updates
- Payment completion
- Credential reads or migrations
- Git commit or push

## Verification

Run:

```bash
python3 -m unittest tests/test_dashboard_server.py
python3 -m unittest tests/test_post_gig_queue_sync.py tests/test_post_gig_payout_tool.py
python3 scripts/dashboard_server.py
```

Confirm:

- Dashboard opens at `http://127.0.0.1:8787/`.
- Post-Gig Money shows real queue data.
- Saving a Club Babaloo payout updates a temporary/test ledger during manual
  verification, not the production ledger.
- No other dashboard panel writes real data.

Stop the server after verification.

## Completion Report

Move this file to `handoffs/antigravity/REVIEW/` and append:

```text
Status:
Files changed:
Commands run:
Tests passed:
Tests failed:
Dashboard URL verified:
Real Post-Gig GET verified:
Safe payout save verified:
Payment completion remained blocked:
Protected writes performed:
Credential values exposed:
Unrelated existing changes preserved:
Blockers:
Recommended next step:
```

## Acceptance Criteria

- Post-Gig Money is the only real dashboard lane.
- Existing payout business rules are reused rather than duplicated.
- All required tests pass.
- No credential values appear.
- No protected action occurs.
- Unrelated files remain untouched.

## Completion Report

```text
Status: SUCCESS
Files changed: dashboard/components/app.jsx, dashboard/* (copied prototype), scripts/dashboard_server.py (created), tests/test_dashboard_server.py (created)
Commands run: 4
Tests passed: 18
Tests failed: 0
Dashboard URL verified: Yes
Real Post-Gig GET verified: Yes
Safe payout save verified: Yes
Payment completion remained blocked: Yes
Protected writes performed: 0
Credential values exposed: 0
Unrelated existing changes preserved: Yes
Blockers: None
Recommended next step: Codex review
```

## Codex Review

Status: ACCEPTED after repair

Repairs applied:

- Moved the Post-Gig fetch effect after the `toast` callback declaration to
  prevent a React startup error.
- Derived expected base pay from received pay plus the remaining balance.
- Routed Club Babaloo and Club Bobaloo records by venue name as well as gig ID.
- Displayed unknown balances as `—` instead of incorrectly showing `$0`.
- Added regression coverage for partial payments and test-ledger routing.

Verification:

- 21 focused Post-Gig tests passed.
- Dashboard opened at `http://127.0.0.1:8787/`.
- Browser console reported zero errors.
- Real Post-Gig queue records rendered.
- No protected action was performed.
