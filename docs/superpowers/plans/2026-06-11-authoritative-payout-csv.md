# Authoritative Payout CSV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and continuously synchronize one five-column administrative payout CSV seeded from the existing Numbers workbook and the current public calendar.

**Architecture:** A focused payout CSV sync module normalizes imported Numbers rows and calendar gigs into `VENUE,CITY,DATE,PAYOUT,TIPS`. It matches rows internally by normalized venue plus date, writes atomically, and becomes the ledger used by the dashboard payout flow. The existing hourly calendar automation invokes the sync after fetching the public calendar.

**Tech Stack:** Python 3 standard library, AppleScript/Numbers export for one-time migration, CSV, public iCal calendar, unittest, macOS LaunchAgent wrapper.

---

### Task 1: Add the five-column payout CSV model

**Files:**
- Create: `scripts/payout_csv_sync.py`
- Create: `tests/test_payout_csv_sync.py`

- [ ] **Step 1: Write failing normalization tests**

Test that:

```python
FIELDNAMES == ["VENUE", "CITY", "DATE", "PAYOUT", "TIPS"]
```

Test that currency values such as `$500.00`, `500`, blank cells, and Numbers
missing-value text normalize to `500.00` or an empty string.

Test that matching keys normalize venue punctuation and whitespace while
retaining the ISO date:

```python
row_key({"VENUE": "The Sewer ", "DATE": "2026-03-06"})
== ("2026-03-06", "the sewer")
```

- [ ] **Step 2: Verify the tests fail**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: import failure because `scripts.payout_csv_sync` does not exist.

- [ ] **Step 3: Implement the row model**

Implement:

```python
FIELDNAMES = ["VENUE", "CITY", "DATE", "PAYOUT", "TIPS"]
ADMIN_LEDGER = Path(
    "/Volumes/VADER/Manifold/Neon_Blonde/Administrative/"
    "PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv"
)

def normalize_money(value: object) -> str: ...
def normalize_venue(value: str) -> str: ...
def normalize_date(value: object) -> str: ...
def row_key(row: dict[str, str]) -> tuple[str, str]: ...
def normalize_row(row: dict[str, object]) -> dict[str, str]: ...
```

`normalize_row` must return exactly the five allowed fields.

- [ ] **Step 4: Verify the model tests pass**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: all normalization tests pass.

### Task 2: Export and import the existing Numbers payout table

**Files:**
- Modify: `scripts/payout_csv_sync.py`
- Modify: `tests/test_payout_csv_sync.py`

- [ ] **Step 1: Write failing import tests**

Add tests for a parser receiving rows shaped like:

```python
[
    {
        "Venue": "The Sewer",
        "City": "Ventura",
        "Date": "3/6/2026",
        "Payout": "$400.00",
        "Tips": "$42.00",
    }
]
```

Expected output:

```python
[
    {
        "VENUE": "The Sewer",
        "CITY": "Ventura",
        "DATE": "2026-03-06",
        "PAYOUT": "400.00",
        "TIPS": "42.00",
    }
]
```

- [ ] **Step 2: Verify the import test fails**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: failure because the Numbers import adapter is absent.

- [ ] **Step 3: Implement Numbers export and import**

Add:

```python
NUMBERS_SOURCE = Path(
    "/Volumes/VADER/Manifold/Neon_Blonde/Administrative/"
    "PAYOUT TRACKING SPREADSHEET/📄-neon-blonde_Payouts 2026.numbers"
)

def parse_numbers_rows(rows: list[dict[str, object]]) -> list[dict[str, str]]: ...
def export_numbers_rows(source: Path = NUMBERS_SOURCE) -> list[dict[str, object]]: ...
```

`export_numbers_rows` should use `osascript` to read the `Neon Blonde Venues`
sheet and `Table 1`, returning the values under Venue, City, Date, Payout, and
Tips. It must not edit or save the Numbers document.

- [ ] **Step 4: Verify the import tests pass**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: parser tests pass.

### Task 3: Merge current calendar gigs without duplicates

**Files:**
- Modify: `scripts/payout_csv_sync.py`
- Modify: `tests/test_payout_csv_sync.py`

- [ ] **Step 1: Write failing merge tests**

Cover:

- Existing Numbers row matching a calendar gig by date and normalized venue.
- Existing payout and tips surviving the match.
- New calendar gig receiving blank payout and tips.
- Running the merge twice producing the same row count.
- Rows absent from the current calendar remaining unchanged.

Use `QueueGig` fixtures from `scripts.post_gig_queue_sync`.

- [ ] **Step 2: Verify merge tests fail**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: failure because calendar merge functions are absent.

- [ ] **Step 3: Implement calendar conversion and merge**

Add:

```python
def calendar_gig_to_row(gig: QueueGig) -> dict[str, str]:
    return {
        "VENUE": gig.venue,
        "CITY": gig.city,
        "DATE": datetime.fromisoformat(gig.start_at).date().isoformat(),
        "PAYOUT": "",
        "TIPS": "",
    }

def merge_rows(
    existing_rows: list[dict[str, str]],
    calendar_gigs: list[QueueGig],
) -> tuple[list[dict[str, str]], dict[str, int]]: ...
```

The merge must:

- Match by `row_key`.
- Preserve existing payout and tips.
- Fill missing city from calendar.
- Add unmatched calendar gigs.
- Sort by date, then venue.
- Return created, matched, and total counts.

- [ ] **Step 4: Verify merge tests pass**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: merge tests pass.

### Task 4: Add atomic authoritative CSV writes and initial migration

**Files:**
- Modify: `scripts/payout_csv_sync.py`
- Modify: `tests/test_payout_csv_sync.py`
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv`

- [ ] **Step 1: Write failing file tests**

Test:

- CSV headers are exactly the five allowed fields.
- Existing CSV rows can be loaded and merged.
- Atomic replacement leaves no partial target.
- Parent-directory absence returns a blocked receipt.

- [ ] **Step 2: Verify file tests fail**

Run:

```bash
python3 -m unittest tests.test_payout_csv_sync
```

Expected: failure because read/write orchestration is absent.

- [ ] **Step 3: Implement file I/O and CLI**

Add:

```python
def read_csv_rows(path: Path) -> list[dict[str, str]]: ...
def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None: ...
def sync_payout_csv(
    ledger_path: Path = ADMIN_LEDGER,
    numbers_source: Path = NUMBERS_SOURCE,
) -> dict[str, object]: ...
```

Behavior:

- If the target CSV does not exist, seed from Numbers.
- If it exists, treat it as authoritative and do not re-import Numbers.
- Fetch calendar gigs using `fetch_calendar_queue_gigs`.
- Merge and write atomically.
- Print a JSON receipt from `main()`.

- [ ] **Step 4: Run initial migration**

Run:

```bash
python3 scripts/payout_csv_sync.py
```

Expected:

- New administrative CSV exists.
- It contains every imported Numbers row.
- It contains every current calendar gig.
- Future gigs have blank payout and tips.

- [ ] **Step 5: Verify idempotence**

Run the command again:

```bash
python3 scripts/payout_csv_sync.py
```

Expected: `created` is `0` and row count remains unchanged.

### Task 5: Route dashboard payout reads and writes to the new CSV

**Files:**
- Modify: `scripts/post_gig_payout_tool.py`
- Modify: `scripts/dashboard_server.py`
- Modify: `scripts/neon_health_check.py`
- Modify: `tests/test_post_gig_payout_tool.py`
- Modify: `tests/test_dashboard_server.py`
- Modify: `tests/test_neon_health_check.py`

- [ ] **Step 1: Write failing dashboard ledger tests**

Test that:

- The default production ledger is the administrative CSV.
- A payout update finds a row by venue plus date.
- Only `PAYOUT` and `TIPS` change.
- No duplicate row is created.
- Club Babaloo continues using `data/post_gig/test_payouts.csv`.
- Dashboard health reports whether the administrative CSV exists.

- [ ] **Step 2: Verify dashboard tests fail**

Run:

```bash
python3 -m unittest \
  tests.test_post_gig_payout_tool \
  tests.test_dashboard_server \
  tests.test_neon_health_check
```

Expected: failures referencing the old `data/post_gig/payouts.csv` contract.

- [ ] **Step 3: Implement five-column payout updates**

Change the payout updater to accept venue, date, payout, and tips, match the
authoritative CSV row by normalized venue plus date, and atomically replace that
row.

The dashboard may continue calculating additional values for display, but only
the five CSV fields may be persisted.

- [ ] **Step 4: Verify dashboard tests pass**

Run:

```bash
python3 -m unittest \
  tests.test_post_gig_payout_tool \
  tests.test_dashboard_server \
  tests.test_neon_health_check
```

Expected: all targeted tests pass.

### Task 6: Add payout CSV synchronization to the hourly automation

**Files:**
- Modify: `scripts/automation/wrapper_venue_sync.sh`
- Modify: `tests/test_automation_wrappers.sh`
- Modify: `references/automation-map.md`
- Modify: `SKILL.md`

- [ ] **Step 1: Write the failing wrapper assertion**

Update the wrapper test to require:

```text
python3 scripts/payout_csv_sync.py
```

after the existing venue calendar sync command.

- [ ] **Step 2: Verify the wrapper test fails**

Run:

```bash
bash tests/test_automation_wrappers.sh
```

Expected: failure because the payout sync command is absent.

- [ ] **Step 3: Update the wrapper and documentation**

Run the payout CSV sync from `wrapper_venue_sync.sh` after loading the shared
environment and after the existing calendar venue sync.

Document:

- The administrative CSV path.
- The exact five-column schema.
- Calendar-created rows have blank payout and tips.
- Numbers is historical input only and is never modified.

- [ ] **Step 4: Verify wrapper behavior**

Run:

```bash
bash tests/test_automation_wrappers.sh
bash scripts/automation/wrapper_venue_sync.sh
```

Expected: both venue sync and payout sync complete successfully.

### Task 7: Full verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run the complete test suite**

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
bash tests/test_automation_wrappers.sh
```

Expected: all tests pass.

- [ ] **Step 2: Inspect the final CSV**

Verify:

```bash
head -n 5 "/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv"
```

Expected header:

```text
VENUE,CITY,DATE,PAYOUT,TIPS
```

Confirm imported historical payout values and current future gigs are present.

- [ ] **Step 3: Verify no duplicate date-plus-venue keys**

Run a read-only check that normalizes date plus venue and reports zero duplicate
keys.

- [ ] **Step 4: Verify the Numbers source is unchanged**

Compare the Numbers file modification time and checksum recorded before
migration with its values after migration.

- [ ] **Step 5: Run Neon V2 health and compatibility checks**

```bash
python3 scripts/neon_health_check.py
python3 scripts/agent_compatibility_check.py --agent codex
```

Expected: success with zero protected writes.
