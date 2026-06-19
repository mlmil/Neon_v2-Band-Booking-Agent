# Neon V2 — Operations Dashboard · Connection Notes

Internal, supervised ops dashboard for **Mike**. Not a public site, not the Band Sheet.
This file documents how the prototype maps to the existing Neon V2 scripts, the data schema,
and which actions are *safe* vs *protected*.

Files:
- `Neon V2 Dashboard.html` — the dashboard (open this)
- `data/data.js` — mock data (`window.NEON_DATA`), the JSON schema below
- `components/` — UI (`ui.jsx`), `modals.jsx`, `panels.jsx`, `app.jsx`

---

## 1 · Core rule (enforced in the UI)

The dashboard **shows status, creates local receipts, drafts actions, and runs read-only checks**.
It must **never** silently update Google Calendar, the Band Sheet, WordPress, send venue email,
share portal folders, or mark a payment complete. Every one of those is a **protected action**
routed through a blocking confirmation modal (`ConfirmModal`) that:

1. names exactly what will change,
2. shows the script/endpoint it will run,
3. requires an explicit "I, Mike, approve this action" checkbox, and
4. writes an `APPROVED:` entry to the local activity log.

If a protected action is *unsafe right now* (e.g. AgentMail down, balance still owed, open Band
Sheet mismatch), the modal shows a **blocked reason** and the confirm button is disabled.

---

## 2 · Failure isolation

Each lane fails independently — one broken workflow never blanks the dashboard. Seeded in the mock:

| Failure | Lane effect | Other lanes |
| --- | --- | --- |
| AgentMail health check DOWN (401) | Email lane `blocked`; **Send email** disabled; Gmail draft fallback offered | Calendar/check/folder lanes stay usable |
| Band Sheet mismatch (BarrelHouse time) | Publishing / "fully confirmed" `blocked` for that gig | Intake + folder data still shown |
| Local model offline | Digest skipped + queued; status `blocked` | **Folder creation still succeeds** |
| New venue folder created | Folder marked `needs_review` (verify name/contact/date) | — |

---

## 3 · Data schema (`window.NEON_DATA`)

Eight collections + a `meta` block. Types below are illustrative.

```
meta            { now, band, operator, project_path, venues_path, last_full_sync }

intake_receipts [{ id, status, received, sender, sender_name, venue, city, date|null,
                   time|null, parsed:{venue,city,date,time,pay,load_in}, missing:[str],
                   summary, ack_draft, receipt_file }]

gigs            [{ id, status, venue, city, date, time, calendar_event:bool, folder_id,
                   bandsheet_match:bool, website_match:bool, promo_status, confirmed:bool,
                   logistics:[str], summary }]

venue_folders   [{ id, status, venue, date, path, receipt:bool, digest:bool,
                   reviewed:bool, note }]

checks          [{ id, kind:'bandsheet'|'website', title, script, status, last_run,
                   result, detail, affected:[gigId] }]

post_gig_items  [{ id, status, venue, city, date, base_pay|null, tips|null, method|null,
                   received_by|null, still_owed|null, paid_complete:bool, notes, summary }]

agent_status    [{ id, key:'agentmail'|'inbox'|'calendar', title, status, script,
                   last_check, message, blocks|null }]

local_model_digest { status, title, model, last_ok, message, pending_digests:[folderId] }

scout_leads     [{ id, status, venue, city, signal, found, fit }]
```

`status` is one of: `success` · `needs_review` · `blocked` · `pending` (plus `reviewed` for intake).

---

## 4 · Action → script map

**SAFE** — run on click, write only local receipts/notes, no external mutation.

| Button (UI) | action id | Maps to |
| --- | --- | --- |
| Create receipt / Mark reviewed (Intake) | `create_receipt`, `mark_reviewed` | `scripts/monitor_inbox.py --write-intake-receipts` |
| Run checks (per gig) | `run_checks` | both verification reports below |
| Run all / Re-run Band Sheet check | `run_all_checks`, `run_bandsheet` | `scripts/bandsheet_verification_report.py` |
| Re-run Website check | `run_website` | `scripts/website_verification_report.py` |
| Health check (AgentMail) | `run_agentmail_health` | `scripts/agentmail_health_check.py` |
| New folder / Open in Finder | `create_folder`, `open_folder` | `scripts/local_venue_folder_sync.py --sync-calendar --use-local-model` |
| Re-run digest / Run pending digests | `rerun_digest` | local model digest step (queues if offline) |
| Mark receipt reviewed (folder) | `mark_folder_reviewed` | local receipt flag |
| Save draft (email) | `save_draft` | `scripts/agentmail_send.py` **draft / Gmail fallback only** |
| Save payout entry | `save_payout` | local payout ledger (no "paid" flag) |
| Add note / Mark needs review / Mark reviewed (lead) | `add_note`, `mark_lead_reviewed` | local activity log |
| Re-check now (sync) | `rerun_sync` | `local_venue_folder_sync.py --sync-calendar` (read-only) |

**PROTECTED** — blocked behind `ConfirmModal`, explicit approval required.

| Button (UI) | action id | Maps to | Guard |
| --- | --- | --- | --- |
| Add to Google Calendar | `add_to_calendar` | **new guarded Calendar writer** (does not exist yet) | always confirm |
| Send email | `send_email` | `scripts/agentmail_send.py` | blocked if AgentMail down |
| Mark payment complete | `mark_paid_complete` | local payout ledger → `paid=true` | blocked if `still_owed > 0` |
| Mark booking fully confirmed | `_confirm_booking` | `bandsheet_verification_report.py --confirm <id>` | blocked if Band Sheet mismatch |
| Publish Band Sheet | `publish_bandsheet` | `bandsheet_verification_report.py --publish` | always confirm |
| Update WordPress show post | `update_wordpress` | `website_verification_report.py --push` | blocked if gig has open mismatch |
| Share venue portal files | `share_portal` | `local_venue_folder_sync.py --share-portal` | blocked if folder unreviewed |
| Change pay / rate terms | `change_pay_terms` | local gig record | always confirm |

> All four formerly-reserved protected actions are now surfaced in the **per-gig detail view**
> (open any gig in the Booking Queue → “Open details”). They share the same `ConfirmModal` gate.

---

## 5 · Wiring the UI to real scripts

Right now every action runs through one dispatcher, `H.act(type, payload)` in `components/app.jsx`,
which calls `apply()` to mutate mock state + log + toast. To go live, replace the body of each
`case` in `apply()` with a call to your local runner. Suggested shape:

```js
// a tiny local bridge (e.g. a Flask/FastAPI server on localhost that shells out to scripts/)
async function runScript(name, args = []) {
  const r = await fetch('http://localhost:8787/run', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, args }),
  });
  return r.json(); // { ok, stdout, receipt_path, ... }
}

// example: replace the 'run_bandsheet' case
case 'run_bandsheet': {
  const res = await runScript('bandsheet_verification_report.py');
  mutate(d => { const c = d.checks.find(x => x.kind === 'bandsheet');
                c.last_run = nowISO(); c.result = res.summary; c.status = res.ok ? 'success' : 'blocked'; });
  addLog('Ran bandsheet_verification_report.py'); break;
}
```

Rules when wiring:
- **Never** put a calendar/Band Sheet/WordPress/email *write* in a SAFE case. Those stay in the
  `PROTECTED` branch, which only fires from inside `ConfirmModal.onConfirm`.
- The bridge runs scripts against the real paths:
  `project = /Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2`,
  `venues = /Volumes/VADER/Manifold/Neon_Blonde/Venues`.
- Read-only checks (`agentmail_health_check.py`, both verification reports, calendar sync) are safe
  to run on load / on a timer to keep the Today strip and statuses fresh.
- `open_folder` should call your OS opener (e.g. `open <path>` on macOS) rather than a browser link.
- Keep the activity log as the audit trail; persist it to a local file (e.g. `/Repos/Neon_v2/ops_log.jsonl`).

---

## 6 · Not doing (by design)

- No public landing page; no Band Sheet data exposed publicly.
- No assumed Google Calendar writes — calendar is the read-only booking trigger.
- No n8n. The dashboard talks to your existing `scripts/` via a thin local bridge only.
