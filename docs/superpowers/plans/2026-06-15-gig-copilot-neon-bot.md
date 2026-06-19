# Gig Copilot Neon Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate Mike-only Telegram bot lane for Gig Copilot onboarding and show-day simulation.

**Architecture:** Create a sibling `Gig Copilot Bot` Python package that mirrors NeonBotstein's transport shape but keeps profile/onboarding logic isolated. Store Mike's logistics profile in local JSON and keep all v1 replies Mike-only.

**Tech Stack:** Python standard library, Telegram Bot API transport pattern, unittest, local JSON file storage.

---

### Task 1: Scaffold Lane And Profile Store

**Files:**
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/models.py`
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/profile_store.py`
- Test: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/tests/test_profile_store.py`

- [ ] Write failing tests for loading missing profiles and saving Mike's profile.
- [ ] Implement `MemberProfile` and `ProfileStore`.
- [ ] Run `python3 -m unittest discover -s tests`.

### Task 2: Add Onboarding Responder

**Files:**
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/responder.py`
- Test: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/tests/test_responder.py`

- [ ] Write failing tests for `/start`, `/help`, `/status`, `/profile`, `/onboard`, and `/simulate-show-day`.
- [ ] Implement pure text-in/text-out reply logic.
- [ ] Keep `/onboard` v1 as a guided questionnaire entrypoint plus command examples for saving defaults.

### Task 3: Add CLI And Telegram Transport

**Files:**
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/telegram_transport.py`
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/cli.py`
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/gig_copilot_bot/__main__.py`
- Test: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/tests/test_cli.py`

- [ ] Write failing tests for local `reply`, `health`, and `poll-once`.
- [ ] Implement token-file loading from `/Users/studio_hub/.hermes/secure/gig_copilot_neon_bot_token.txt`.
- [ ] Implement `health` identity check for `GigCopilotNeon_Bot`.

### Task 4: Docs And Verification

**Files:**
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/README.md`
- Create: `/Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2/Gig Copilot Bot/GIG_COPILOT_HANDOFF.md`

- [ ] Document commands, token path, JSON profile path, and Mike-only v1 limits.
- [ ] Run tests.
- [ ] Run local command simulations.
