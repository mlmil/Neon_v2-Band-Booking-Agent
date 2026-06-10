# Neon V2 Agent Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Codex, Claude, and Hermes full Neon V2 operators with the same skill rules, local tools, credential discovery, and approval gates.

**Architecture:** `SKILL.md` remains the shared authority. Agent-specific entry files point to it, a secret-free manifest defines required capabilities and canonical credential sources, and one compatibility script produces redacted receipts. A Club Babaloo fixture verifies safe operational behavior without touching protected systems.

**Tech Stack:** Markdown, JSON, Python standard library, `unittest`.

---

### Task 1: Define shared agent and credential contract

**Files:**
- Create: `AGENT_COMPATIBILITY.md`
- Create: `config/credential-manifest.json`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `HERMES.md`

- [ ] Document full-operator parity and protected actions.
- [ ] Define canonical file and environment-variable credential sources without values.
- [ ] Point every agent entry file to `SKILL.md` and the compatibility contract.

### Task 2: Add compatibility checker

**Files:**
- Create: `scripts/agent_compatibility_check.py`
- Test: `tests/test_agent_compatibility_check.py`

- [ ] Write failing tests for redacted credential checks and Club Babaloo behavior.
- [ ] Implement local capability, credential source, and fixture checks.
- [ ] Verify receipts never contain secret values.

### Task 3: Integrate and verify

**Files:**
- Modify: `SKILL.md`
- Modify: `references/automation-map.md`
- Modify: `.gitignore`

- [ ] Add the compatibility command and parity policy.
- [ ] Ignore shared runtime secret files and compatibility receipts.
- [ ] Run focused tests and each agent profile.
- [ ] Commit only compatibility files; leave unrelated Scout edits untouched.
