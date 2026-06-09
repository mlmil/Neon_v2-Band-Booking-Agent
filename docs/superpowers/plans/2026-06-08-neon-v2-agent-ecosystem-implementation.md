# Neon V2 Agent Ecosystem Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first safe implementation layer for Venue Agent, Scout Agent, Booking Pipeline, failure handling, and dashboard-ready status tracking.

**Architecture:** Keep source-of-truth writes protected. Start with local schemas, templates, validators, and reports before connecting calendar writes, Band Sheet publishing, email sending, or portal sharing. Existing scripts stay intact unless a task explicitly wraps them.

**Tech Stack:** Python 3 standard library, pytest-style assertions via `python3 -m unittest`, Markdown templates, CSV, existing Neon V2 scripts and references.

---

## File Structure

Create:

- `schemas/venue_agent_schema.json` - required fields for `VENUE_AGENT.md` frontmatter or structured sections.
- `schemas/reconciliation_schema.json` - required receipt fields and status values.
- `schemas/scout_leads_schema.json` - CSV column contract and allowed statuses.
- `templates/VENUE_AGENT.md` - starter venue profile.
- `templates/RECONCILIATION.md` - starter gig receipt.
- `templates/FAILURE_RECEIPT.md` - standard failure receipt.
- `scripts/venue_agent_tool.py` - local CLI for validating event inputs and creating local venue/gig folders.
- `scripts/scout_agent_tool.py` - local CLI for validating Scout CSV and creating lead notes.
- `scripts/bandsheet_verification_report.py` - deterministic calendar-vs-Band-Sheet comparison report scaffold.
- `tests/test_venue_agent_tool.py` - tests for calendar event validation, alias matching, and folder plan output.
- `tests/test_scout_agent_tool.py` - tests for Scout CSV validation and status handling.
- `tests/test_failure_statuses.py` - tests protected write gating rules.

Modify:

- `SKILL.md` - point to implementation scripts only after they exist and pass tests.
- `references/agent-ecosystem.md` - add concrete script entrypoints after implementation.
- `references/failure-handling.md` - keep status model aligned with tests.

Do not modify in this first pass:

- `scripts/create_venue_package.sh` - old flyer/package path remains untouched.
- Band Sheet repo - separate implementation phase.
- Google Calendar data - no write actions in this plan.
- Gmail/AgentMail sends - no send actions in this plan.

---

## Task 1: Define Shared Schemas And Templates

**Files:**

- Create: `schemas/venue_agent_schema.json`
- Create: `schemas/reconciliation_schema.json`
- Create: `schemas/scout_leads_schema.json`
- Create: `templates/VENUE_AGENT.md`
- Create: `templates/RECONCILIATION.md`
- Create: `templates/FAILURE_RECEIPT.md`
- Test: `tests/test_failure_statuses.py`

- [x] **Step 1: Create schema folder and template folder**

Run:

```bash
mkdir -p schemas templates tests
```

Expected: directories exist.

- [x] **Step 2: Add failure status test**

Create `tests/test_failure_statuses.py`:

```python
import unittest

ALLOWED_STATUSES = {"success", "needs_review", "blocked", "failed", "uncertain"}
PROTECTED_WRITES = {
    "calendar_update",
    "bandsheet_publish",
    "venue_email_send",
    "portal_share",
    "payment_complete",
    "booking_confirmed",
    "rate_change",
}


def can_perform_protected_write(lane_status):
    return lane_status == "success"


class FailureStatusTests(unittest.TestCase):
    def test_allowed_statuses_include_blocking_states(self):
        self.assertIn("blocked", ALLOWED_STATUSES)
        self.assertIn("uncertain", ALLOWED_STATUSES)

    def test_protected_writes_stop_when_uncertain(self):
        for status in ["needs_review", "blocked", "failed", "uncertain"]:
            self.assertFalse(can_perform_protected_write(status))

    def test_protected_writes_continue_only_on_success(self):
        self.assertTrue(can_perform_protected_write("success"))
        self.assertIn("bandsheet_publish", PROTECTED_WRITES)


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 3: Run test**

Run:

```bash
python3 -m unittest tests/test_failure_statuses.py
```

Expected: `OK`.

- [x] **Step 4: Add JSON schemas**

Create `schemas/reconciliation_schema.json`:

```json
{
  "required_fields": [
    "venue_name",
    "gig_date",
    "city",
    "start_time",
    "calendar_status",
    "venue_folder_status",
    "bandsheet_status",
    "payment_status",
    "promo_status",
    "portal_status",
    "open_questions"
  ],
  "allowed_statuses": ["success", "needs_review", "blocked", "failed", "uncertain"],
  "payment_statuses": ["unpaid", "paid", "partial", "needs_review"],
  "protected_writes": [
    "calendar_update",
    "bandsheet_publish",
    "venue_email_send",
    "portal_share",
    "payment_complete",
    "booking_confirmed",
    "rate_change"
  ]
}
```

Create `schemas/scout_leads_schema.json`:

```json
{
  "columns": [
    "lead_id",
    "venue_name",
    "city",
    "county",
    "region_priority",
    "status",
    "lead_score",
    "source_type",
    "source_url",
    "similar_bands_seen",
    "booking_contact_name",
    "booking_contact_email",
    "booking_contact_phone",
    "lead_owner",
    "next_action",
    "follow_up_date",
    "last_checked",
    "notes"
  ],
  "allowed_statuses": [
    "discovered",
    "researching",
    "qualified",
    "ready_to_contact",
    "contacted",
    "follow_up",
    "warm",
    "not_a_fit",
    "booked",
    "converted_to_venue_agent"
  ]
}
```

Create `schemas/venue_agent_schema.json`:

```json
{
  "required_fields": [
    "canonical_venue_name",
    "aliases",
    "city",
    "contact_people",
    "email_policy",
    "sms_policy",
    "typical_rate",
    "payment_notes",
    "load_in_notes",
    "marketing_notes",
    "portal_rules"
  ]
}
```

- [x] **Step 5: Add templates**

Create `templates/FAILURE_RECEIPT.md`:

```markdown
# Failure Receipt

- Action:
- Status:
- Source:
- What changed:
- What did not change:
- Failure reason:
- Next step:
```

Create `templates/VENUE_AGENT.md`:

```markdown
# Venue Agent

- Canonical venue name:
- Aliases:
- City:
- Contact people:
- Email policy:
- SMS policy:
- Typical rate:
- Payment notes:
- Load-in notes:
- Marketing notes:
- Portal rules:

## Open Questions

-
```

Create `templates/RECONCILIATION.md`:

```markdown
# Gig Reconciliation

- Venue name:
- Gig date:
- City:
- Start time:
- Calendar status:
- Venue folder status:
- Band Sheet status:
- Payment status:
- Promo status:
- Portal status:

## Source Fields

- Calendar title:
- Calendar location:
- Calendar start:
- Calendar creator:

## Open Questions

-

## Failure Receipt

- Action:
- Status:
- Source:
- What changed:
- What did not change:
- Failure reason:
- Next step:
```

- [ ] **Step 6: Commit**

Run:

```bash
git add schemas templates tests/test_failure_statuses.py
git commit -m "feat: add agent workflow schemas"
```

Expected: commit succeeds.

---

## Task 2: Build Venue Agent Local Planner

**Files:**

- Create: `scripts/venue_agent_tool.py`
- Test: `tests/test_venue_agent_tool.py`

- [x] **Step 1: Write tests**

Create `tests/test_venue_agent_tool.py`:

```python
import tempfile
import unittest
from pathlib import Path

from scripts.venue_agent_tool import (
    CalendarEvent,
    build_folder_plan,
    normalize_venue_name,
    validate_calendar_event,
)


class VenueAgentToolTests(unittest.TestCase):
    def test_calendar_event_accepts_city_only_location(self):
        event = CalendarEvent(title="Tonys Pizza", location="Ventura", start="2026-06-06T19:00:00")
        result = validate_calendar_event(event)
        self.assertEqual(result["status"], "success")

    def test_calendar_event_blocks_full_address_location(self):
        event = CalendarEvent(
            title="Tonys Pizza",
            location="Ventura, California, United States",
            start="2026-06-06T19:00:00",
        )
        result = validate_calendar_event(event)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "BLOCKED_CALENDAR")

    def test_normalize_venue_name_handles_punctuation(self):
        self.assertEqual(normalize_venue_name("Harry's Night Club"), "harrys night club")

    def test_build_folder_plan_uses_existing_venue_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tonys Pizza").mkdir()
            event = CalendarEvent("Tony's Pizza", "Ventura", "2026-06-06T19:00:00")
            plan = build_folder_plan(event, root)
            self.assertEqual(plan["status"], "success")
            self.assertEqual(plan["venue_folder"], str(root / "Tonys Pizza"))
            self.assertEqual(plan["gig_folder"], str(root / "Tonys Pizza" / "gigs" / "2026-06-06"))


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
python3 -m unittest tests/test_venue_agent_tool.py
```

Expected: import failure because `scripts/venue_agent_tool.py` does not exist yet.

- [x] **Step 3: Implement local planner**

Create `scripts/venue_agent_tool.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


VENUES_ROOT = Path("/Volumes/VADER/Manifold/Neon_Blonde/Venues")


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    location: str
    start: str


def normalize_venue_name(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9 ]+", "", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _date_from_start(start: str) -> str:
    return datetime.fromisoformat(start.replace("Z", "+00:00")).date().isoformat()


def validate_calendar_event(event: CalendarEvent) -> dict:
    if not event.title.strip():
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Missing venue title"}
    if not event.location.strip():
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Missing city location"}
    if "," in event.location or "california" in event.location.lower() or "united states" in event.location.lower():
        return {
            "status": "blocked",
            "code": "BLOCKED_CALENDAR",
            "failure_reason": "Location must be city only",
        }
    try:
        _date_from_start(event.start)
    except ValueError:
        return {"status": "blocked", "code": "BLOCKED_CALENDAR", "failure_reason": "Invalid start datetime"}
    return {"status": "success"}


def _resolve_venue_folder(venue_name: str, venues_root: Path) -> Path | None:
    target = normalize_venue_name(venue_name)
    for child in venues_root.iterdir() if venues_root.exists() else []:
        if child.is_dir() and normalize_venue_name(child.name) == target:
            return child
    return None


def build_folder_plan(event: CalendarEvent, venues_root: Path = VENUES_ROOT) -> dict:
    validation = validate_calendar_event(event)
    if validation["status"] != "success":
        return validation
    venue_folder = _resolve_venue_folder(event.title, venues_root)
    if venue_folder is None:
        venue_folder = venues_root / re.sub(r"[/:\"]+", "", event.title).strip()
        status = "needs_review"
        code = "NEEDS_VENUE_REVIEW"
    else:
        status = "success"
        code = "VENUE_RESOLVED"
    gig_date = _date_from_start(event.start)
    return {
        "status": status,
        "code": code,
        "venue_folder": str(venue_folder),
        "gig_folder": str(venue_folder / "gigs" / gig_date),
        "reconciliation_path": str(venue_folder / "gigs" / gig_date / "RECONCILIATION.md"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--venues-root", default=str(VENUES_ROOT))
    args = parser.parse_args()
    event = CalendarEvent(args.title, args.location, args.start)
    print(json.dumps(build_folder_plan(event, Path(args.venues_root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests/test_venue_agent_tool.py
```

Expected: `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/venue_agent_tool.py tests/test_venue_agent_tool.py
git commit -m "feat: add venue agent planner"
```

Expected: commit succeeds.

---

## Task 3: Build Scout CSV Validator

**Files:**

- Create: `scripts/scout_agent_tool.py`
- Test: `tests/test_scout_agent_tool.py`

- [x] **Step 1: Write tests**

Create `tests/test_scout_agent_tool.py`:

```python
import csv
import tempfile
import unittest
from pathlib import Path

from scripts.scout_agent_tool import REQUIRED_COLUMNS, validate_scout_csv


class ScoutAgentToolTests(unittest.TestCase):
    def test_valid_empty_csv_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            path.write_text(",".join(REQUIRED_COLUMNS) + "\n")
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "success")

    def test_missing_column_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            path.write_text("lead_id,venue_name,status\n")
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["code"], "SCOUT_SOURCE_INCOMPLETE")

    def test_invalid_status_needs_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scout-leads.csv"
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                row = {column: "" for column in REQUIRED_COLUMNS}
                row["lead_id"] = "lead-1"
                row["venue_name"] = "Example Room"
                row["status"] = "maybe"
                writer.writerow(row)
            result = validate_scout_csv(path)
            self.assertEqual(result["status"], "needs_review")
            self.assertIn("maybe", result["failure_reason"])


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
python3 -m unittest tests/test_scout_agent_tool.py
```

Expected: import failure because `scripts/scout_agent_tool.py` does not exist yet.

- [x] **Step 3: Implement CSV validator**

Create `scripts/scout_agent_tool.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED_COLUMNS = [
    "lead_id",
    "venue_name",
    "city",
    "county",
    "region_priority",
    "status",
    "lead_score",
    "source_type",
    "source_url",
    "similar_bands_seen",
    "booking_contact_name",
    "booking_contact_email",
    "booking_contact_phone",
    "lead_owner",
    "next_action",
    "follow_up_date",
    "last_checked",
    "notes",
]

ALLOWED_STATUSES = {
    "discovered",
    "researching",
    "qualified",
    "ready_to_contact",
    "contacted",
    "follow_up",
    "warm",
    "not_a_fit",
    "booked",
    "converted_to_venue_agent",
}


def validate_scout_csv(path: Path) -> dict:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return {
                "status": "blocked",
                "code": "SCOUT_SOURCE_INCOMPLETE",
                "failure_reason": f"Missing columns: {', '.join(missing)}",
            }
        invalid_statuses = []
        for row in reader:
            status = row.get("status", "")
            if status and status not in ALLOWED_STATUSES:
                invalid_statuses.append(status)
        if invalid_statuses:
            return {
                "status": "needs_review",
                "code": "SCOUT_STATUS_INVALID",
                "failure_reason": f"Invalid statuses: {', '.join(sorted(set(invalid_statuses)))}",
            }
    return {"status": "success"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()
    print(json.dumps(validate_scout_csv(Path(args.csv_path)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 4: Run tests**

Run:

```bash
python3 -m unittest tests/test_scout_agent_tool.py
```

Expected: `OK`.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/scout_agent_tool.py tests/test_scout_agent_tool.py
git commit -m "feat: add scout lead validator"
```

Expected: commit succeeds.

---

## Task 4: Build Band Sheet Verification Report Scaffold

**Files:**

- Create: `scripts/bandsheet_verification_report.py`
- Test: `tests/test_bandsheet_verification_report.py`

- [x] **Step 1: Write tests**

Create `tests/test_bandsheet_verification_report.py`:

```python
import unittest

from scripts.bandsheet_verification_report import compare_gigs


class BandSheetVerificationReportTests(unittest.TestCase):
    def test_matching_gigs_pass(self):
        calendar = [{"date": "2026-06-06", "venue": "Tony's Pizza", "city": "Ventura", "time": "7pm"}]
        bandsheet = [{"date": "2026-06-06", "venue": "Tonys Pizza", "city": "Ventura", "time": "7pm"}]
        result = compare_gigs(calendar, bandsheet)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["mismatches"], [])

    def test_missing_bandsheet_gig_blocks_publish(self):
        calendar = [{"date": "2026-06-06", "venue": "Tony's Pizza", "city": "Ventura", "time": "7pm"}]
        bandsheet = []
        result = compare_gigs(calendar, bandsheet)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "BANDSHEET_MISMATCH")


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Implement comparison scaffold**

Create `scripts/bandsheet_verification_report.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import re


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _key(gig: dict) -> tuple[str, str]:
    return gig["date"], _norm(gig["venue"])


def compare_gigs(calendar_gigs: list[dict], bandsheet_gigs: list[dict]) -> dict:
    calendar_by_key = {_key(gig): gig for gig in calendar_gigs}
    bandsheet_by_key = {_key(gig): gig for gig in bandsheet_gigs}
    mismatches = []

    for key, gig in calendar_by_key.items():
        if key not in bandsheet_by_key:
            mismatches.append({"type": "calendar_missing_from_bandsheet", "gig": gig})
            continue
        other = bandsheet_by_key[key]
        for field in ["city", "time"]:
            if _norm(str(gig.get(field, ""))) != _norm(str(other.get(field, ""))):
                mismatches.append({"type": f"{field}_mismatch", "calendar": gig, "bandsheet": other})

    for key, gig in bandsheet_by_key.items():
        if key not in calendar_by_key:
            mismatches.append({"type": "bandsheet_missing_from_calendar", "gig": gig})

    if mismatches:
        return {"status": "blocked", "code": "BANDSHEET_MISMATCH", "mismatches": mismatches}
    return {"status": "success", "mismatches": []}
```

- [x] **Step 3: Run tests**

Run:

```bash
python3 -m unittest tests/test_bandsheet_verification_report.py
```

Expected: `OK`.

- [ ] **Step 4: Commit**

Run:

```bash
git add scripts/bandsheet_verification_report.py tests/test_bandsheet_verification_report.py
git commit -m "feat: add bandsheet verification scaffold"
```

Expected: commit succeeds.

---

## Task 5: Wire Docs To Implemented Entry Points

**Files:**

- Modify: `SKILL.md`
- Modify: `references/agent-ecosystem.md`
- Modify: `references/failure-handling.md`

- [x] **Step 1: Update `SKILL.md` implementation notes**

Add under `## Implementation Notes`:

```markdown
- Venue Agent local planner: `python3 scripts/venue_agent_tool.py --title "Tonys Pizza" --location "Ventura" --start "2026-06-06T19:00:00"`
- Scout CSV validator: `python3 scripts/scout_agent_tool.py "/Volumes/VADER/Manifold/Neon_Blonde/Scout Agent/scout-leads.csv"`
- Band Sheet verification scaffold: `scripts/bandsheet_verification_report.py`
```

- [x] **Step 2: Update `references/agent-ecosystem.md`**

Add:

```markdown
## Local Tools

- Venue Agent planner: `scripts/venue_agent_tool.py`
- Scout lead validator: `scripts/scout_agent_tool.py`
- Band Sheet verification scaffold: `scripts/bandsheet_verification_report.py`
```

- [x] **Step 3: Run all tests**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: `OK`.

- [ ] **Step 4: Commit**

Run:

```bash
git add SKILL.md references/agent-ecosystem.md references/failure-handling.md
git commit -m "docs: wire agent ecosystem tools"
```

Expected: commit succeeds.

---

## Task 6: Dashboard Read-Only Prototype Plan

**Files:**

- Create: `docs/superpowers/specs/2026-06-08-dashboard-readonly-slice.md`

- [x] **Step 1: Create the dashboard slice spec**

Create `docs/superpowers/specs/2026-06-08-dashboard-readonly-slice.md`:

```markdown
# Neon V2 Dashboard Read-Only Slice

Goal: show one screen with current operational state without writing to calendar, Band Sheet, email, portal, or payment records.

Sections:

- Next gig
- Blocked lanes
- Needs review
- Band Sheet verification status
- Venue Agent queue
- Scout Agent queue
- Payment/admin queue
- Local model digest

Allowed data sources:

- Live Band Sheet JSON
- Local Venue folders
- Local Scout Agent CSV
- Local reconciliation receipts
- Local failure receipts

Protected writes:

- No Google Calendar updates
- No Band Sheet publish
- No email send
- No portal sharing
- No payment completion
```

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-06-08-dashboard-readonly-slice.md
git commit -m "docs: define dashboard readonly slice"
```

Expected: commit succeeds.

---

## Self-Review

Spec coverage:

- Venue Agent folder and reconciliation: Tasks 1 and 2.
- Failure handling and protected writes: Task 1 and docs already added.
- Scout Agent ecosystem: Task 3.
- Booking Pipeline: documented as a lane; no folder until qualified leads exist.
- Band Sheet verification gate: Task 4.
- Dashboard: Task 6 read-only slice.
- Promo automation: intentionally separate meeting/session.
- Local model pilot: remains read-only and future task after folder/receipt tools exist.

Placeholder scan:

- No `TBD` implementation steps.
- No generic "write tests" steps without concrete test content.
- No protected write actions in this plan.

Execution order:

1. Schemas/templates.
2. Venue local planner.
3. Scout validator.
4. Band Sheet verification scaffold.
5. Documentation wiring.
6. Dashboard read-only slice.
