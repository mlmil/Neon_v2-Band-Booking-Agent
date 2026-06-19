# Handoff: Neon V2 — Operations Dashboard

## Overview

An internal, supervised operations dashboard for **Mike**, who manages the band **Neon Blonde**
(a 6-piece 80s post-punk cover band). It is a single-screen "command center" that surfaces the
state of booking, calendar accuracy, venue folders, post-gig payments, and supporting agents/scripts
— and lets the operator take **safe local actions** directly, while gating **protected external
actions** (anything that mutates Google Calendar, the Band Sheet, WordPress, sends email, shares
files, or marks money paid) behind an explicit confirmation step.

This is **not** a public website and **not** the band's "Band Sheet." It is an internal tool.

### The one rule that governs the whole UI
The dashboard may **show status, create local receipts, draft actions, and run read-only checks**.
It must **never silently**: update Google Calendar, publish the Band Sheet, update WordPress, send
venue email, share portal folders, mark a payment complete, change pay terms, or mark a booking
fully confirmed. Every one of those is a **protected action** and must pass through a blocking
confirmation modal that (1) names what will change, (2) shows the script it runs, (3) requires an
explicit operator approval checkbox, and (4) writes an `APPROVED:` entry to an audit log.

If you implement nothing else faithfully, implement this guardrail.

---

## About the Design Files

The files in `prototype/` are **design references built in HTML/React-via-Babel** — a working
prototype that demonstrates the intended look, layout, interaction model, and (critically) the
safe-vs-protected action gating. **They are not meant to be shipped as-is.**

Your task is to **recreate this design in the target codebase's real environment**, using its
established patterns, component library, state management, and build tooling. The prototype runs
React 18 with in-browser Babel and plain inline-style objects; a production implementation should
use your app's normal stack (e.g. React + a real bundler + your CSS/styling system, or whatever the
project uses). If there is no existing environment yet, React + Vite + CSS variables is a clean
match for this design, but any framework is fine — the design tokens and behavior below are
framework-agnostic.

The prototype is **runnable** for reference: serve the `prototype/` folder over HTTP
(`python3 -m http.server` from inside it) and open `Neon V2 Dashboard.html`. Opening via `file://`
may fail because it loads sub-scripts with `<script src>`.

---

## Fidelity

**High-fidelity.** Colors, typography, spacing, borders, iconography, and interaction states are all
final and intentional — they follow the **Spark Ai "Civic Grid" design system** (see Design Tokens).
Recreate the UI to match: square corners everywhere, 1px hairline rules instead of shadows, mono
uppercase labels, a single amber accent, and a small set of semantic status colors. Match it closely.

The **data is mock.** `prototype/data/data.js` contains invented but realistically-shaped records.
Treat the *shape* (the schema) as the spec; treat the *values* as placeholder content.

---

## Design System: Spark Ai "Civic Grid"

The visual language is editorial / civic-document / industrial. Principles, all load-bearing:

- **Square corners. `border-radius: 0` everywhere.** No exceptions in this dashboard (the source
  system allows circular avatars, but this screen has none).
- **No shadows.** Depth comes from hairline borders and fill contrast only.
- **Hairline rules** (1px, `--rule`) are the primary structural divider. Cards have a 1px border and
  a 3px top border whose color encodes status.
- **Flat solid backgrounds.** No gradients, no textures, no background images. Surfaces differ by hue
  only: page (`--bg`) → card (`--surface`).
- **One accent: amber.** Used for the active/primary CTA, section markers, the wordmark period, and
  "warn/needs-review" status. Never a gradient, never a second decorative accent.
- **Type:** Inter Tight (display/headings), Inter (body), JetBrains Mono (all labels, metadata, IDs,
  paths, code). Mono labels are UPPERCASE with open letter-spacing; display text uses tight negative
  tracking — the contrast between the two is the signature.
- **No emoji, ever.** Iconography is custom 24×24 inline SVG, stroke-width 1.6, round caps/joins.
- **Motion is scarce:** ~120–180ms fades/color transitions, `cubic-bezier(.2,.6,.2,1)`. No bounces,
  no parallax. The one entrance animation is an 8px slide-up fade on toasts.

---

## Layout (top level)

A sticky top nav, then a centered content column (`max-width: 1560px`, horizontal padding
`--page-pad-x` = 56px desktop), containing:

1. **Top Nav** (sticky, `height: 76px`, 1px bottom rule)
2. **"Today" strip** (4-cell status banner)
3. **Main body** — either an **8-panel masonry grid** (default) or a **3-column swimlane** layout,
   toggled via the Tweaks panel.

Plus overlay layers: modals (intake / gig detail / money / draft / note / confirm), a right-side
activity-log drawer, a bottom-left toast stack, and the Tweaks panel.

### Responsive behavior
- Masonry grid: `column-count` 3 → 2 (≤1340px) → 1 (≤980px). Each panel is `break-inside: avoid`
  with a 20px bottom margin and 20px column gap.
- Swimlanes: `repeat(3, 1fr)` → single column (≤1080px).
- Today strip: 4 cols → 2 cols (≤980px) → 1 col (≤520px), implemented as a CSS grid with a 1px gap
  over a `--rule`-colored background so the gaps read as hairlines.
- Nav: the "Operations Dashboard" sublabel and "Internal · Supervised" badge hide below ~920px /
  640px respectively.

---

## Status Taxonomy (used everywhere)

Every record carries a `status`. Five values, each with a fixed color and mono label:

| status | label | dark color | light color | meaning |
| --- | --- | --- | --- | --- |
| `success` | `OK` | `#7FB069` (moss-green) | `#4F7A3F` | all clear |
| `needs_review` | `NEEDS REVIEW` | `#E39A2B` (amber `--accent`) | `#C67A17` | operator attention |
| `blocked` | `BLOCKED` | `#E0584C` (desaturated red) | `#C0392B` | something must be resolved |
| `pending` | `PENDING` | `#8a8d92` (muted) | `#6b6b66` | not started |
| `reviewed` | `REVIEWED` | `#7FB069` (= success) | `#4F7A3F` | intake item promoted |

**StatusChip** = a small square dot (8–10px, the status color) + the mono uppercase label in that
color. Note: the green and red are *additions* on top of the Spark Ai base palette — a status board
genuinely needs them — but they're kept desaturated to stay within the civic register. Amber does
double duty as the brand accent and the "needs review" status.

Status drives three visual treatments:
- **Panel top border** (3px): blocked → red, needs_review → amber, else → `--rule`.
- **Panel header background tint**: blocked → `color-mix(--bad 9%)`, needs_review → `--warn 7%`, else transparent.
- **List item left border** (3px) + faint blocked-row background tint.

---

## Screens / Views

### 1. Top Nav
- **Layout:** flex row, space-between, full content width, 76px tall, 1px bottom rule, sticky to top,
  page background.
- **Left cluster:** spark-plug logo PNG (`assets/spark-plug-bone.png`, height 30px, opacity .92) ·
  wordmark `NEON.V2` where the `.` is amber (`--accent`) and the rest is `--fg`, Inter 700, 15px ·
  a 1px×14px divider · mono label "OPERATIONS DASHBOARD" (`--fg-muted`, 10px). Divider + sublabel
  hide ≤920px (`.nb-hide-md`).
- **Right cluster** (flex, gap 10px), four outlined buttons/links sharing one style (mono 10.5px
  uppercase, `padding: 7px 11px`, 1px `--rule` border, `--fg-muted-2` text, min-height 32px, square):
  1. **Fresh Ground Sound** — link to the rehearsal-space Google Calendar (`meta.calendar_url`),
     opens new tab. Icon: `calendar` glyph + label + small `open` (external-link) glyph.
     *Hover (links only):* border + text go amber.
  2. **Band Sheet** — link to the private Band Sheet (`meta.bandsheet_url`), opens new tab.
     Icon: `sheet` glyph + label + `open` glyph.
  3. A 1px×18px divider + **Internal · Supervised** badge (amber 1px border, amber `lock` glyph +
     amber mono label). Both hide ≤640px (`.nb-hide-sm`).
  4. **Activity (N)** — button that opens the activity-log drawer; `note` glyph + count.
     *Hover:* border `--fg-muted`, text `--fg`.

### 2. "Today" strip
A 4-cell banner (1px outer border + 3px amber top border; cells separated by 1px hairline gaps).
Each cell: 18px×22px padding, a mono uppercase label on top, then content.

- **Cell 1 — "◉ Today's First Move"** (label in amber). Computes the highest-priority blocked gig
  and shows: a display headline (Inter Tight 20px/600) e.g. "Resolve BarrelHouse Brewing time
  mismatch", a one-line plain-language explanation (12px `--fg-muted`), and an amber outline button
  "Go to Accuracy Checks" that smooth-scrolls to that panel. If nothing is blocked: "All lanes clear."
- **Cell 2 — "Next gig":** venue name (Inter Tight 18px/600), then `calendar` glyph + mono
  "DATE · TIME", then amber mono "IN N DAYS · CITY". Picks the soonest future gig.
- **Cell 3 — "Critical blockers":** label and cell tint go red when count > 0. A huge number
  (Inter Tight 34px/600, red if >0 else green) + "NEED ATTENTION", then up to 3 bulleted blocker
  summaries (red 5px square + 11.5px text). Blockers are aggregated from: blocked gigs, blocked
  agents (AgentMail), local-model-offline, and blocked checks.
- **Cell 4 — "Last successful sync":** green `check` glyph + the sync time (mono 13px), then mono
  "CALENDAR READ · {relative time}", then an outline "Re-check now" button (`refresh` glyph) that
  runs the read-only calendar sync.

### 3–10. The Eight Panels

All panels share a **Panel shell**: card surface, 1px border, 3px status-colored top border. Header
row = icon (amber, or red if blocked) + title (Inter Tight ~15.5px/600) + optional count (mono) +
optional section label (mono uppercase, e.g. "§ PHASE 1 — PRE-CALENDAR") on the left; optional
header action button + StatusChip on the right. Header has a 1px bottom rule and a status tint.
Body = vertical flex, gap 12px (10px compact), `--card-pad`-ish 20px padding (16px compact).

Each panel renders a list of **Item** rows (1px border, 3px status-colored left border, 12–13px
padding, gap 8px). Items that open a detail view have `cursor: pointer`; inner action buttons
`stopPropagation` so they don't trigger the row click.

> **§ 1 · Intake Queue** — icon `inbox`, section "§ Phase 1 — pre-calendar".
> Booking emails parsed *before* a calendar event exists. Each item: venue (display), mono meta
> "CITY · DATE|no date · ID", a StatusChip, and — if fields are missing — an amber `alert` glyph +
> "N missing: Pay terms, Load-in time". Buttons: **Review** (opens Intake modal), **Create receipt**.
> Clicking the row opens the Intake modal. Count = number of non-reviewed items. Panel status =
> needs_review if any open, else success.

> **§ 2 · Booking Queue** — icon `calendar`, section "§ Phase 2 — calendar exists".
> Gigs that have a calendar event. Each item: venue, mono meta "CITY · DATE TIME · in Nd", StatusChip,
> a row of four **CheckDots** (Band Sheet / Website / Folder / Flyer — each a 7px square, green if ok
> else red, with a mono caption), the first logistics warning if any (amber/red `alert` + text), and
> buttons **Open details** (amber, opens Gig Detail modal), **Run checks**, **Open folder**. Row click
> opens Gig Detail. Panel status = worst item status.

> **§ 3 · Accuracy Checks** — icon `check-doc`, section "§ Verification". Header action: **Run all**.
> Two checks (Band Sheet verification, Website verification). Each item: title + the script path in
> mono (`scripts/...py`), StatusChip, a plain-language result line, a "Last run {rel}" mono caption,
> and buttons **Re-run Band Sheet/Website check** + (if not success) **Add note**. Panel status =
> worst check status.

> **§ 4 · Venue Folders** — icon `folder`, section "§ /Venues". Header action: **New folder**.
> Local folders under `/Venues/[Venue]/[Venue - YYYY-MM-DD]/`. Each item: venue, the full path in
> tiny mono (break-all), StatusChip, three CheckDots (Receipt / Digest / Reviewed), a note line, and
> buttons **Open in Finder**, **Mark receipt reviewed** (if unreviewed), **Re-run digest** (if no
> digest). Count = total; status = needs_review if any folder needs review.

> **§ 5 · Post-Gig Money** — icon `money`, section "§ Phase 3 — gig passed".
> Gigs whose date has passed and need payout reconciliation. Each item: venue, mono "DATE · CITY",
> StatusChip, a row of **Stat** blocks (Base / Tips / Owed / Method — Owed is red if >0 else green),
> and buttons **Enter/Edit payout** (amber, opens Money modal) + **Add note**. Row click opens the
> Money modal. Status = needs_review if any item not settled.

> **§ 6 · AgentMail Status** — icon `mail`, section "§ Email lane". Header action: **Health check**.
> Lists the three agents (AgentMail, Inbox monitor, Calendar sync (read)). Each as a bordered block
> with a status-colored left border: title + StatusChip + message + (if it blocks something) a red
> mono "Blocks: Send email (Gmail draft fallback available)". Panel status = AgentMail's status.

> **§ 7 · Local Model Status** — icon `cpu`, section "§ Digest engine".
> Single status block for the local model: a square status dot + model name, a message, two Meta rows
> (Last OK / Pending digests), a reassurance block ("Folder creation is unaffected…"), and buttons
> **Retry connection** + **Run pending digests**.

> **§ 8 · Scout / Leads** — icon `scout`, section "§ Prospecting".
> Potential new venues. Each item: venue, mono "CITY · fit High/Med · found {rel}", StatusChip, a
> signal/why line, and buttons **Draft outreach** (opens Draft modal prefilled), **Add note**,
> **Mark reviewed**.

### Modals (overlay, z-index 200)
Shared **Overlay**: fixed full-screen scrim `rgba(8,9,10,0.66)`, content box centered-top
(`padding: 64px 20px`, scrollable), the box is `--surface` with 1px border + 3px amber top border.
**Esc** closes; clicking the scrim closes; clicking inside does not. Shared **ModalHead**: icon +
mono label + display title + an outlined square close (`x`) button. `danger` variant turns the icon
and label red.

- **Intake modal** (600px): facts grid (Venue/City/Date/Time/Sender/Received — missing Date/Time
  shown in red), parsed summary, a "Missing fields" warn block (amber-bordered chips), an editable
  **acknowledgment draft** textarea (labeled "local, not sent"). Footer: safe buttons **Create
  receipt / Draft reply / Mark reviewed** on the left, and the protected **Add to Google Calendar**
  (red, lock) on the right.
- **Gig Detail modal** (640px): status banner (border + tint in the status color) with summary +
  StatusChip; facts grid (City/Date/In/Calendar/Confirmed/Promo); a Verification row of CheckDots;
  a logistics-warnings block; a "Safe actions — local only" button row (Run checks / Open folder /
  Draft follow-up / Add note); a **Pay / rate terms** sub-card with a text input + protected
  **Change pay terms**; and a **Protected** section (red lock header) listing four rows each with a
  label + a red protected button: **Mark booking fully confirmed**, **Publish Band Sheet**,
  **Update WordPress show post**, **Share venue portal files**.
- **Money modal** (580px): gig date/city, a grid of numeric inputs (Base pay / Tips / Still owed),
  Payment method `<select>` (Cash/Check/Venmo/Zelle/Bank transfer/Other), Received by input, Notes
  textarea; a warn banner appears when "still owed" > 0. Footer: safe **Save payout entry (local)**
  + protected **Mark payment complete**.
- **Draft modal** (600px): To / Subject / Body inputs; if AgentMail is down, a red banner explains
  send is disabled and saving creates a Gmail draft fallback. Footer: safe **Save draft (local)** +
  protected **Send email**.
- **Note modal** (480px): a single textarea + **Save note**.
- **Confirm modal** (540px, the guardrail): red `lock` head "Protected action — confirmation
  required" + the action title; body explanation; a **"This will change"** list (each line a red
  `arrow` + the mutation); a "Runs {script}" line in amber mono; then EITHER a red **blocked-reason**
  banner (if the action is currently unsafe) OR an **approval checkbox** ("I, Mike, approve this
  action. It will be recorded as an explicit approval in the local activity log."). Footer: **Cancel**
  + the confirm CTA (red→filled when armed), which is **disabled until the checkbox is ticked**, and
  replaced by a disabled **Blocked** button when a blocked-reason is present.

### Activity Log drawer (z-index 180)
Right-side panel (420px), slides over a lighter scrim. Header: mono "LOCAL ACTIVITY LOG" + display
"Receipts & approvals" + close. Body: a scrollable list of entries, each = a 7px status-colored
square + the message + a mono caption ("APPROVED · {rel} · {clock}" for protected approvals). Entry
kinds color the square: safe→green, review→amber, draft→muted, protected/bad→red.

### Toasts (z-index 150)
Bottom-left stack. Each: `--surface` card, 1px border + 3px left border colored by kind
(bad→red, review→amber, protected→red, else green), a `check`/`alert` glyph + message. Auto-dismiss
after 3.6s. Entrance: 220ms slide-up-fade.

### Tweaks panel
A small floating control panel (from a shared `tweaks-panel.jsx` host component) titled "Tweaks",
with: **Arrangement** (grid / swimlanes), **Density** (compact / comfortable), **Hide all-clear
items** (toggle), **Mode** (dark / light). It persists to localStorage and is only relevant to the
prototype — in production, wire these to whatever settings mechanism you use, or drop them. The
dark/light toggle sets `data-theme` on `<html>`.

---

## Interactions & Behavior

- **Action dispatch:** every button calls a single dispatcher `H.act(type, payload)`. It branches:
  - If `type` is a **protected** action → open the **Confirm modal** (after computing any
    blocked-reason). The action only applies from inside the modal's `onConfirm`.
  - Else → apply immediately: mutate local state, show a toast, append an activity-log entry.
- **Protected action set & guards** (see also the action map below):
  - `add_to_calendar` — always confirm.
  - `send_email` — **blocked** if AgentMail health is `blocked` (offer Gmail draft fallback instead).
  - `mark_paid_complete` — **blocked** if `still_owed > 0`.
  - `_confirm_booking` (mark fully confirmed) — **blocked** if the gig has an open Band Sheet mismatch.
  - `publish_bandsheet` — always confirm (on success, clears the Band Sheet check).
  - `update_wordpress` — **blocked** if the gig has an open mismatch (on success, clears website check).
  - `share_portal` — **blocked** if the venue folder is unreviewed.
  - `change_pay_terms` — always confirm.
- **Smooth scroll:** "Today's First Move" CTA scrolls to a panel by its `[data-anchor]` with a ~90px
  top offset. **Do not use `scrollIntoView`**; compute offset and use `window.scrollTo`.
- **Optimistic local mutation:** the prototype deep-clones state and edits it. In production, these
  map to real script invocations (see Connection Notes) — keep the optimistic UI but reconcile with
  the script's actual result and surface failures as `blocked`.
- **Failure isolation (important):** one failing lane must never blank the dashboard. Each panel
  renders independently from its own slice of data; a `blocked` lane is visually quarantined (red
  border/tint) but all other lanes stay fully usable. The seeded examples: AgentMail down → email
  send disabled but everything else works; Band Sheet mismatch → publish/confirm blocked but intake
  and folders still shown; local model offline → digests skip/queue but folder creation still works;
  a newly created folder → auto-marked `needs_review`.
- **Hover states:** outline buttons → border/text brighten; amber buttons → invert to filled amber
  with ink text; protected buttons → invert to filled red with white text; link buttons → amber.
  All ~150ms.
- **Focus:** inputs/textareas/selects get an amber border on focus; buttons get a 2px amber
  focus-visible outline.

---

## State Management

Top-level app state (in the prototype, React `useState`; map to your store of choice):

- `data` — the full dataset (deep-cloned from the mock; see Schema). All panels derive from this.
- `modal` — `{ kind, ctx }` for the active modal (`intake` | `gig` | `money` | `draft` | `note`), or null.
- `confirm` — the active Confirm-modal descriptor `{ title, cta, body, touches[], scriptHint,
  blockedReason, onConfirm }`, or null.
- `toasts` — array of `{ id, msg, kind }`; each auto-removed after 3.6s.
- `log` — array of `{ t (ISO), kind, msg }`, newest first. `kind` ∈ safe | review | draft |
  protected | bad. Protected approvals are logged with an `APPROVED:` prefix — this is the audit trail
  and should be **persisted** (the Connection Notes suggest a local `ops_log.jsonl`).
- `logOpen` — drawer visibility.
- Tweaks: `layout`, `density`, `theme`, `hideClear` (persisted to localStorage in the prototype).

State transitions are all triggered through `H.act` (above) plus the modal open helpers
(`openIntake`, `openMoney`, `openDraft`, `openNote`, `openGig`, `confirmAction`). Read-only checks
(`agentmail_health_check`, both verification reports, calendar sync) are safe to run on load and on a
timer to keep the Today strip and statuses fresh.

---

## Design Tokens

All tokens are defined in `prototype/assets/colors_and_type.css` (the Spark Ai system). Use these
exact values.

### Color — dark theme (default)
| token | value | use |
| --- | --- | --- |
| `--bg` | `#0E0F11` | page background |
| `--surface` | `#17191C` | card / panel / modal surface |
| `--surface-inv` | `#F2EFE6` | inverted surface (unused here) |
| `--fg` | `#F2EFE6` | primary text (warm bone) |
| `--fg-muted` | `#8a8d92` | muted text / labels |
| `--fg-muted-2` | `#c7cad0` | secondary text |
| `--rule` | `#2a2d32` | 1px hairlines, borders |
| `--rule-soft` | `#ffffff14` | intra-card dividers |
| `--accent` | `#E39A2B` | amber accent + "needs review" |
| `--accent-ink` | `#0E0F11` | text on amber fills |

### Color — light theme
`--bg #F6F4EF` · `--surface #FFFFFF` · `--fg #111111` · `--fg-muted #6b6b66` ·
`--fg-muted-2 #3a3a36` · `--rule #111111` · `--rule-soft #11111126` · `--accent #C67A17` ·
`--accent-ink #F6F4EF`.

### Semantic status colors (added by this dashboard, not in the base system)
| token | dark | light |
| --- | --- | --- |
| `--ok` | `#7FB069` | `#4F7A3F` |
| `--warn` | `var(--accent)` (`#E39A2B`) | `var(--accent)` (`#C67A17`) |
| `--bad` | `#E0584C` | `#C0392B` |
| `--idle` | `#8a8d92` | `#6b6b66` |

These are declared per-theme in the HTML head:
```css
[data-theme="dark"]  { --ok:#7FB069; --warn:var(--accent); --bad:#E0584C; --idle:#8a8d92; }
[data-theme="light"] { --ok:#4F7A3F; --warn:var(--accent); --bad:#C0392B; --idle:#6b6b66; }
```
Status tints use `color-mix(in srgb, <status> 6–9%, transparent)`.

### Typography
| family | token | usage |
| --- | --- | --- |
| Inter Tight | `--font-display` | headings, titles, big numbers |
| Inter | `--font-body` | body, descriptions, inputs |
| JetBrains Mono | `--font-mono` | labels, metadata, IDs, paths, code, buttons |

Loaded from Google Fonts (weights 400/500/600/700; mono 400/500/600). Representative sizes:
- Display titles: 14.5–20px / 600 / letter-spacing −0.01 to −0.02em.
- Big stat number (blockers): 34px / 600.
- Body: 11.5–13.5px / line-height 1.45–1.55.
- Mono labels: 9–11px, UPPERCASE, letter-spacing 0.05–0.1em, weight 400–500.
- Button text: mono 10.5px, UPPERCASE, letter-spacing 0.06em, weight 500 (600 for protected).

### Spacing / layout
- Page horizontal padding `--page-pad-x`: 56px (18px ≤640px). Content max-width 1560px.
- Nav height `--nav-h`: 76px. Min hit target `--hit`: 44px (buttons use min-height 32px for dense
  toolbar actions; primary/touch targets should respect 44px).
- Panel padding: 20px (16px compact). Inter-panel gap: 20px. Card-ish inner gap: 10–12px.
- Item padding: 12–13px. Button padding: 7px 11px.
- **Border radius: 0 everywhere.** Borders: 1px `--rule`; status accents are 3px.

### Motion
`--ease: cubic-bezier(.2,.6,.2,1)` · `--dur: 180ms` · `--dur-quick: 120ms`. Hover transitions ~150ms.
Toast entrance 220ms slide-up-fade.

---

## Iconography

Custom inline SVG, 24×24 viewBox, `fill: none`, `stroke-width: 1.6` (2 for the padlock),
`stroke-linecap/linejoin: round`, colored by context (amber by default, red when blocked). The full
set used: `inbox, calendar, folder, check-doc, mail, money, cpu, scout, refresh, check, alert, clock,
lock, plus, note, eye, send, x, arrow, open, pin, flag, globe, sheet`. The complete SVG path data is
in `prototype/components/ui.jsx` (the `Icon` component) — lift the paths directly. Do **not**
substitute an emoji or a different icon set's metaphors without matching this stroke style; if you
must use a library, **Lucide** is the closest match (same 1.5–2px stroke, round caps).

---

## Assets

- `prototype/assets/spark-plug-bone.png` — the Spark Ai spark-plug logo (cream-on-dark), used in the
  nav at 30px height. From the Spark Ai design system.
- `prototype/assets/colors_and_type.css` — the full Spark Ai token stylesheet. In a real app, fold
  these into your own theme layer rather than importing wholesale, but keep the values.
- Fonts: Inter Tight, Inter, JetBrains Mono (Google Fonts).

---

## Data Schema

The mock lives at `prototype/data/data.js` as `window.NEON_DATA`. Shape (illustrative types):

```
meta            { now, band, operator, project_path, venues_path,
                  calendar_url, bandsheet_url, last_full_sync }

intake_receipts [{ id, status, received, sender, sender_name, venue, city, date|null,
                   time|null, parsed:{venue,city,date,time,pay,load_in}, missing:[str],
                   summary, ack_draft, receipt_file }]

gigs            [{ id, status, venue, city, date, time, calendar_event:bool, folder_id,
                   bandsheet_match:bool, website_match:bool, promo_status, confirmed:bool,
                   logistics:[str], summary, pay_terms? }]

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

`status` ∈ `success | needs_review | blocked | pending` (+ `reviewed` for intake).

---

## Action → Script Map (safe vs protected)

The dashboard is meant to connect to a set of existing local Python scripts via a thin localhost
bridge. The full mapping, the bridge pattern, and copy-paste wiring examples are in
**`Connection Notes.md`** (bundled here). Summary:

**SAFE** (run on click, local-only, no external mutation): create/mark intake receipt, run checks
(Band Sheet / Website verification reports), AgentMail health check, create/open venue folder,
re-run digest, mark receipt/folder reviewed, save email draft (Gmail fallback), save payout entry,
add note, mark lead reviewed, read-only calendar re-sync.

**PROTECTED** (must pass the Confirm modal): add to Google Calendar, send email, mark payment
complete, mark booking fully confirmed, publish Band Sheet, update WordPress, share venue portal
files, change pay/rate terms. Each maps to a specific script/endpoint and several carry the guard
conditions listed under *Interactions & Behavior*.

**When wiring:** never place an external *write* in a SAFE handler. Writes live only in the
protected branch that fires from `ConfirmModal.onConfirm`. Persist the activity log as the audit
trail. Run the read-only checks on load / on a timer.

---

## Files in this bundle

```
design_handoff_neon_v2_dashboard/
├── README.md                     ← this file
├── Connection Notes.md           ← script wiring, bridge pattern, full action map
├── screenshots/                  ← reference renders of the key states
│   ├── 01-dashboard-grid.png       default dark command center (nav + Today strip + panels)
│   ├── 02-gig-detail-blocked.png   per-gig detail for a BLOCKED gig (mismatch quarantined)
│   ├── 03-confirmation-gate.png    the protected-action confirmation modal (Publish Band Sheet)
│   ├── 04-intake-modal.png         intake review modal (parsed request, missing fields, ack draft)
│   └── 05-light-theme.png          the same dashboard in light theme
└── prototype/                    ← runnable design reference (serve over HTTP)
    ├── Neon V2 Dashboard.html    ← entry; theme/status tokens + script load order
    ├── data/data.js              ← window.NEON_DATA mock (the schema spec)
    ├── components/
    │   ├── ui.jsx                ← tokens-in-JS, StatusChip, Icon library, Btn/ProtectedBtn,
    │   │                            Panel, Meta, Item, date/format helpers
    │   ├── modals.jsx            ← Overlay, ModalHead, ConfirmModal, Intake/Money/Draft/Note/GigDetail
    │   ├── panels.jsx            ← TodayStrip + the 8 panels + CheckDot/Stat/Empty
    │   └── app.jsx               ← App state, H.act dispatcher, PROTECTED registry, TopNav,
    │                                Swimlanes, LogDrawer, toasts, Tweaks wiring
    ├── tweaks-panel.jsx          ← prototype-only tweak controls host
    └── assets/
        ├── colors_and_type.css   ← Spark Ai design tokens
        └── spark-plug-bone.png   ← logo
```

To run the reference locally:
```bash
cd design_handoff_neon_v2_dashboard/prototype
python3 -m http.server 8000
# open http://localhost:8000/Neon%20V2%20Dashboard.html
```
