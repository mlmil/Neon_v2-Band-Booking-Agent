# Neon V2 README and Infographics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Publish a detailed, accurate GitHub README and two polished infographics explaining Neon V2 and its Gig Copilot.

**Architecture:** The root README will be the public entry point and will link to two project-owned PNG assets in `docs/images/`. Copy will derive from the operational authority files and distinguish implemented, supervised, and planned capabilities. Visuals will use a shared dark coastal operations style and concise labels suitable for GitHub display.

**Tech Stack:** GitHub-flavored Markdown, PNG raster assets generated with the built-in image-generation tool, Python/Pillow inspection, Git.

## Global Constraints

- Describe Neon Blonde as a five-member band based in Ventura, California, performing up and down the Southern California coast.
- Do not expose credentials, private URLs, addresses, chat IDs, or tokens.
- Do not imply Google Calendar write access or unrestricted autonomous protected actions.
- Frame live location sharing as a required, temporary gig-day coordination practice.
- Distinguish implemented, supervised, and planned capabilities.

---

### Task 1: Generate the Main Neon V2 Infographic

**Files:**
- Create: `docs/images/neon-v2-agentic-workflow.png`

**Interfaces:**
- Consumes: approved design in `docs/superpowers/specs/2026-06-19-readme-infographics-design.md`
- Produces: wide PNG embedded by the root README

- [x] **Step 1: Generate the infographic**

Use the built-in image-generation tool with a wide GitHub composition, dark coastal palette, and the exact workflow labels from the design.

- [x] **Step 2: Save the generated image**

Copy the selected generated asset into `docs/images/neon-v2-agentic-workflow.png`.

- [x] **Step 3: Inspect the image**

Verify legibility, correct labels, five-member symbolism, no watermark, and no private information.

### Task 2: Generate the Gig Copilot Infographic

**Files:**
- Create: `docs/images/gig-copilot-show-day-workflow.png`

**Interfaces:**
- Consumes: approved location-sharing and show-day design
- Produces: wide PNG embedded by the Gig Copilot README section

- [x] **Step 1: Generate the infographic**

Use the built-in image-generation tool to show temporary live location sharing, traffic, weather, shared ETAs, alerts, coordinated arrival, setup, and showtime.

- [x] **Step 2: Save the generated image**

Copy the selected generated asset into `docs/images/gig-copilot-show-day-workflow.png`.

- [x] **Step 3: Inspect the image**

Verify the graphic communicates required gig-day use and does not imply permanent tracking.

### Task 3: Write the Public README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: both infographic paths and live operational references
- Produces: repository landing page

- [x] **Step 1: Replace the minimal README**

Write the approved sections: band context, mission, lifecycle, capabilities, Gig Copilot, safeguards, architecture, repository map, setup, validation, status, and audience.

- [x] **Step 2: Embed both images**

Use relative paths:

```markdown
![Neon V2 agentic workflow](docs/images/neon-v2-agentic-workflow.png)
![Gig Copilot show-day workflow](docs/images/gig-copilot-show-day-workflow.png)
```

- [x] **Step 3: Check factual claims**

Compare README statements against `SKILL.md`, `AGENT_COMPATIBILITY.md`, `references/automation-map.md`, and the two bot READMEs.

### Task 4: Verify and Publish

**Files:**
- Modify: `docs/superpowers/plans/2026-06-19-readme-infographics.md`

**Interfaces:**
- Consumes: completed README and graphics
- Produces: reviewed commit pushed to draft PR #1

- [x] **Step 1: Validate files and Markdown**

Run:

```bash
test -f docs/images/neon-v2-agentic-workflow.png
test -f docs/images/gig-copilot-show-day-workflow.png
rg -n "five-member|Ventura|Southern California|Live Location Sharing|Human Approval" README.md
git diff --check
```

Expected: both files exist, required concepts are present, and no whitespace errors are reported.

- [x] **Step 2: Inspect image dimensions**

Run a Pillow check and confirm both images decode successfully and are wide-format assets.

- [x] **Step 3: Review the final diff**

Confirm only the README, two graphics, plan, and intended supporting documentation are included.

- [x] **Step 4: Commit and push**

```bash
git add README.md docs/images docs/superpowers/plans/2026-06-19-readme-infographics.md
git commit -m "Add Neon V2 README and infographics"
git push
```
