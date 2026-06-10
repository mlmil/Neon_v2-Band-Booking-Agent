# Task 001: Agent Compatibility Pilot

## Objective

Verify that Anti-Gravity can execute a bounded Neon V2 task, respect credential
security, and produce evidence for Codex review.

## Required Reading

1. `SKILL.md`
2. `AGENT_COMPATIBILITY.md`
3. `config/credential-manifest.json`
4. `handoffs/antigravity/README.md`

## Existing Work To Preserve

Do not modify or delete:

- `schemas/scout_leads_schema.json`
- `scripts/scout_agent_tool.py`
- `.obsidian/`
- `.smart-env/`
- `.superpowers/`
- `.vault-intelligence/`
- `archive-repos/`
- `Neon V2 dashboard.zip`
- `design_handoff_neon_v2_dashboard/`

## Steps

1. Move this file from `READY/` to `IN_PROGRESS/`.
2. Run:

```bash
python3 -m unittest tests/test_agent_compatibility_check.py
python3 scripts/agent_compatibility_check.py --agent codex
python3 scripts/agent_compatibility_check.py --agent claude
python3 scripts/agent_compatibility_check.py --agent hermes
```

3. Confirm that every receipt:

- Reports the same credential availability.
- Reports `secret_values_exposed: false`.
- Passes the Club Babaloo fixture.
- Reports all protected writes as `false`.

4. Do not create, recover, request, display, or guess missing credentials.
5. Do not edit application code during this pilot.
6. Move this handoff to `REVIEW/`.
7. Append the completion report defined in
   `handoffs/antigravity/README.md`.

## Expected Result

The compatibility unit tests pass. The three agent checks may remain blocked
only because WordPress credentials are unavailable in the canonical shared
runtime source. That is an acceptable and expected pilot result.

## Protected Actions

Not approved:

- Email send
- Calendar write
- Band Sheet publish
- WordPress update
- Payment completion
- Credential creation or migration
- Git commit or push

## Acceptance Criteria

- No source files changed.
- No secret values appear in terminal output or the completion report.
- Existing unrelated work remains untouched.
- A clear report is present under `handoffs/antigravity/REVIEW/`.
