# Anti-Gravity Execution Protocol

Anti-Gravity executes bounded Neon V2 implementation plans. Codex owns
architecture, review, integration, and deployment.

## Folders

```text
READY/        Codex-approved tasks waiting for execution
IN_PROGRESS/  Task moved here when Anti-Gravity starts
REVIEW/       Completed work and execution report awaiting Codex review
COMPLETE/     Codex-approved finished tasks
```

## Execution Rules

1. Read `SKILL.md`, `AGENT_COMPATIBILITY.md`, and the assigned handoff.
2. Check `git status` before editing.
3. Do not alter pre-existing unrelated changes.
4. Follow the handoff exactly. Do not expand scope.
5. Never print, copy, commit, or summarize passwords, tokens, API keys, or
   credential fragments.
6. Do not perform protected writes unless the handoff explicitly records Mike's
   approval.
7. Run every required test and command.
8. Move the handoff to `REVIEW/` and append the completion report.
9. Do not commit or push unless the handoff explicitly authorizes it.

## Completion Report

Append:

```text
Status:
Files changed:
Commands run:
Tests passed:
Tests failed:
Protected writes performed:
Credential values exposed:
Unrelated existing changes preserved:
Blockers:
Recommended next step:
```

