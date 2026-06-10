# Unified Health Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one read-only command that runs four independent Neon V2 health lanes and emits a consolidated JSON receipt.

**Architecture:** Add a small orchestrator that accepts injectable lane functions for deterministic tests and uses existing live-check functions by default. Every lane has its own exception boundary, so failures are isolated and collected before the overall status is calculated.

**Tech Stack:** Python standard library, existing Neon V2 check modules, `unittest`.

---

### Task 1: Receipt Aggregation

**Files:**
- Create: `scripts/neon_health_check.py`
- Create: `tests/test_neon_health_check.py`

- [ ] **Step 1: Write failing aggregation tests**

Test that all lanes run, mixed results produce an overall blocked receipt, and
exceptions become isolated blocked lane results.

- [ ] **Step 2: Verify the tests fail**

Run:

```bash
python3 -m unittest tests/test_neon_health_check.py
```

Expected: import failure because `scripts/neon_health_check.py` does not exist.

- [ ] **Step 3: Implement minimal aggregation**

Create `run_health_checks(checks)` and `main()` with JSON output and success or
failure exit codes.

- [ ] **Step 4: Verify tests pass**

Run:

```bash
python3 -m unittest tests/test_neon_health_check.py
```

Expected: all tests pass.

### Task 2: Live Lane Adapters

**Files:**
- Modify: `scripts/neon_health_check.py`
- Modify: `tests/test_neon_health_check.py`

- [ ] **Step 1: Write failing adapter tests**

Test dashboard file validation and confirm no secret-shaped fields appear in
the consolidated receipt.

- [ ] **Step 2: Verify the new tests fail**

Run the focused test module and confirm the missing adapter behavior fails.

- [ ] **Step 3: Connect existing checks**

Use:

- `agentmail_health_check.run_health_check`
- `bandsheet_verification_report.run_live_check`
- `website_verification_report.run_live_check`
- `dashboard_server.get_post_gig_data`

- [ ] **Step 4: Verify focused and related tests**

Run:

```bash
python3 -m unittest tests/test_neon_health_check.py tests/test_agentmail_health_check.py tests/test_bandsheet_verification_report.py tests/test_website_verification_report.py tests/test_dashboard_server.py
```

Expected: all tests pass.

### Task 3: Documentation And Live Verification

**Files:**
- Modify: `references/automation-map.md`

- [ ] **Step 1: Document the command**

Add `scripts/neon_health_check.py` to the automation map as a read-only
cross-phase supervisor.

- [ ] **Step 2: Run the live command**

```bash
python3 scripts/neon_health_check.py
```

Expected: valid JSON, every lane represented, no protected writes. Live service
mismatches may produce exit code `1` while still proving failure isolation.

- [ ] **Step 3: Run regression tests**

Run the focused health-check suite and `git diff --check`.

- [ ] **Step 4: Commit**

Commit only the unified health-check files and documentation.
