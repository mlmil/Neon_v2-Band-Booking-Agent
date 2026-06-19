# Telegram Bot Milestone 1 Design

Date: 2026-06-15
Repo: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2`
Lane: `Telegram Bot`

## Goal

Implement Milestone 1 of the Neon Telegram bot as a strictly read-only BandSheet
intelligence layer.

This milestone stops before live routing, calendar mutation, outbound Telegram
sends, or any recommendation that implies schedule certainty beyond the source
confidence available from BandSheet data.

## Source Spec Summary

The attached build spec defines the Telegram bot as a Neon copilot and explicitly
limits Milestone 1 to:

1. Directory and repository discovery
2. BandSheet structured-data discovery
3. A validated read-only BandSheet provider

The same spec also makes two boundaries explicit:

1. Do not add live routing yet
2. Fail closed when schedule confidence is weak or freshness is stale

## Existing Repo Constraints

The current Neon V2 repo already establishes these operating rules:

1. Python-first scripts and tests are the dominant implementation pattern.
2. BandSheet JSON is the preferred source over page scraping.
3. BandSheet freshness must be checked. If the data is older than 4 days, treat
   it as stale and reduce trust.
4. Read-only behavior is a hard requirement around external systems.
5. Existing Neon docs already separate provider logic from later action layers.

## Milestone 1 Outcome

Milestone 1 should produce a local Python package in the `Telegram Bot` lane that
can:

1. Confirm it is running inside the intended Neon V2 repo.
2. Resolve the canonical BandSheet URLs and local working directories.
3. Fetch and parse BandSheet structured data from the public JSON endpoint.
4. Validate freshness and schema at the provider boundary.
5. Return a normalized snapshot object for downstream bot logic.
6. Emit clear failure reasons when the source is missing, malformed, stale, or
   incomplete.

Milestone 1 should not:

1. Calculate departure times
2. Invent open dates
3. Send Telegram messages
4. Write to Google Calendar
5. Blend multiple data sources into final routing advice

## Proposed File Layout

All new implementation stays inside `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Telegram Bot`.

```text
Telegram Bot/
  README.md
  __init__.py
  config.py
  discovery.py
  models.py
  providers/
    __init__.py
    bandsheet.py
  fixtures/
    bandsheet-data.sample.json
  tests/
    test_discovery.py
    test_bandsheet_provider.py
```

## Module Responsibilities

### `config.py`

Centralize lane-local constants:

1. Repo root resolution
2. Bot root resolution
3. Canonical BandSheet page URL
4. Canonical BandSheet JSON URL
5. Freshness threshold in days
6. HTTP timeout

This keeps all source assumptions explicit and easy to audit.

### `discovery.py`

Own path and repository checks:

1. Resolve repo root from the current file location
2. Confirm required parent files exist, such as `SKILL.md` and `README.md`
3. Confirm the current lane name is `Telegram Bot`
4. Return a structured `RepoContext`

This makes the bot fail early if someone copies the lane elsewhere or runs it
against the wrong checkout.

### `models.py`

Define the minimum normalized data layer for Milestone 1:

1. `RepoContext`
2. `BandSheetSource`
3. `BandSheetFreshness`
4. `BandSheetEvent`
5. `BandSheetSnapshot`
6. `ProviderWarning`

The intent is to normalize the BandSheet response once and avoid leaking raw JSON
across the codebase.

### `providers/bandsheet.py`

Single source adapter for BandSheet JSON:

1. Fetch JSON over HTTPS
2. Parse the response
3. Validate required top-level fields
4. Compute freshness status from the published `updated` value
5. Normalize events into `BandSheetEvent`
6. Return warnings for stale or partial data
7. Raise explicit provider errors for unusable data

This provider remains read-only and does not try to infer travel or routing.

## Data Contract

Milestone 1 should normalize only the fields needed for later travel logic, while
preserving uncertainty.

### `BandSheetSnapshot`

Suggested fields:

1. `source_url`
2. `fetched_at`
3. `updated_at`
4. `freshness_days`
5. `is_stale`
6. `events`
7. `warnings`

### `BandSheetEvent`

Suggested fields:

1. `title`
2. `date`
3. `start_time`
4. `end_time`
5. `venue_name`
6. `city`
7. `timezone`
8. `raw_payload`

Fields such as `city` and `timezone` must be allowed to remain `None`. Milestone
1 should not invent values.

## Error Strategy

Use explicit provider exceptions instead of returning ambiguous empty snapshots.

Suggested error classes:

1. `DiscoveryError`
2. `BandSheetFetchError`
3. `BandSheetSchemaError`
4. `BandSheetFreshnessError`

Behavior:

1. Network failure: raise `BandSheetFetchError`
2. Invalid JSON: raise `BandSheetSchemaError`
3. Missing required shape: raise `BandSheetSchemaError`
4. Excessive staleness: either raise `BandSheetFreshnessError` or return a
   snapshot with a blocking warning, depending on call mode

Recommended default for Milestone 1:

Return a snapshot for stale data only if the raw payload is otherwise valid, but
mark it `is_stale=True` and include a blocking warning. This preserves observability
without pretending the data is safe for routing.

## Testing Plan

Follow strict TDD. Start with failing tests in the new lane-local test package.

### `test_discovery.py`

Cover:

1. Repo root resolves from the bot lane
2. Missing parent markers fail loudly
3. Wrong lane name fails loudly

### `test_bandsheet_provider.py`

Cover:

1. Valid sample JSON produces a normalized snapshot
2. Missing `updated` fails or blocks correctly
3. Stale data is surfaced as stale
4. Missing event fields remain `None` rather than being invented
5. Invalid JSON raises schema error
6. HTTP failure raises fetch error

Use a checked-in JSON fixture based on the public BandSheet structure so tests do
not depend on live network access.

## Implementation Order

1. Add lane-local README describing Milestone 1 scope
2. Write failing discovery tests
3. Implement `config.py`, `discovery.py`, and minimal `RepoContext`
4. Write failing BandSheet provider tests
5. Implement `models.py`
6. Implement `providers/bandsheet.py`
7. Run focused tests for the new lane
8. Add usage notes and known boundaries to the lane README

## Risks

1. The public BandSheet JSON shape may drift, so parsing should be defensive.
2. The existing spec appears to assume travel logic later. If event normalization
   is too thin now, Milestone 2 may need a contract change.
3. The `Telegram Bot` lane is currently empty, so packaging decisions made here
   will likely become the default structure for later milestones.

## Recommendation

Proceed with a small Python package inside `Telegram Bot`, with tests first and a
single BandSheet provider as the only external dependency boundary for Milestone 1.

This matches the attached spec, the repo's read-only operating rules, and the
existing Neon pattern of explicit source validation before downstream actions.

## Approval Gate

If approved, the next implementation step is:

1. Scaffold the lane-local package and tests
2. Write the first failing discovery test
3. Implement only enough code to make that test pass
