# Neon V2 Agent Compatibility

Codex, Claude, Gemini, and Hermes are full Neon V2 operators on Mike's Mac.

## Shared Authority

All agents must load:

1. `SKILL.md`
2. `references/automation-map.md`
3. `references/failure-handling.md`
4. `config/credential-manifest.json`

No agent may invent a separate Neon V2 workflow or silently use different
credentials.

## Credential Parity

Credential parity is mandatory:

- Every approved Neon V2 credential and API must have one canonical source.
- Codex, Claude, Gemini, and Hermes must all be able to read that source at runtime.
- A credential known only to one agent is a deployment blocker.
- New credentials must be added to `config/credential-manifest.json`.
- Runtime environment values may be stored in `.secrets/neon-v2.env`.
- Google Workspace authentication is only for Drive and Contacts.
- Gmail intake uses read-only IMAP with `BODY.PEEK` and must not alter read state or labels.
- Calendar uses the public iCal feed.
- GroupMe, AgentMail, and WordPress retain their required authentication.
- GroupMe API authentication fetches current messages into local exports.

Never commit, print, summarize, fingerprint, or copy secret values into:

- `SKILL.md`
- agent instruction files
- compatibility receipts
- Git history
- logs or user-facing output

Availability receipts report only:

```text
available
missing
unreadable
```

## Full Operator Scope

All four agents may:

- Read the Neon V2 skill and references.
- Run local validation and synchronization scripts.
- Read the public Band Sheet and public calendar.
- Use configured APIs and authenticated services.
- Fetch GroupMe messages and synchronize the local export database.
- Create local venue folders, receipts, queues, and drafts.
- Perform approved AgentMail, WordPress, and Band Sheet actions.

Protected actions still require Mike's explicit approval:

- Send venue-facing email.
- Publish Band Sheet changes.
- Update WordPress.
- Share venue portal files.
- Change booking or pay terms.
- Mark a payment complete.

Neon V2 does not create, edit, or delete Google Calendar events. Calendar
changes are manual.

## Compatibility Test

Run for each agent:

```bash
python3 scripts/agent_compatibility_check.py --agent codex
python3 scripts/agent_compatibility_check.py --agent claude
python3 scripts/agent_compatibility_check.py --agent gemini
python3 scripts/agent_compatibility_check.py --agent hermes
```

The Club Babaloo fixture is always test data. It must produce a local plan and
must report every protected write as `false`.

An agent is a full operator only when its receipt returns `status: success`.
## Google Workspace MCP

The repo-local MCP declaration for read-only Google Workspace access is
`mcp.google-workspace.json`. It starts `/Volumes/VADER/Google Auth/workspace_mcp.py`
with the shared credentials in `/Volumes/VADER/Google Auth`.

The current Google Workspace MCP server exposes read-only Gmail, Google
Calendar, Drive, and Contacts tools. Calendar reads should use the public
calendar ID/iCal feed as the primary source. Google Calendar API access is
allowed only as a read-only diagnostic and fallback path for error checking.
Treat those tools as read-only. Calendar, email, Drive, and contact mutations
remain protected actions and need an explicit project policy change before
implementation.
