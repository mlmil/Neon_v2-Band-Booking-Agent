# Neon V2 Agent Compatibility

Codex, Claude, and Hermes are full Neon V2 operators on Mike's Mac.

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
- Codex, Claude, and Hermes must all be able to read that source at runtime.
- A credential known only to one agent is a deployment blocker.
- New credentials must be added to `config/credential-manifest.json`.
- Runtime environment values may be stored in `.secrets/neon-v2.env`.
- Existing OAuth/client files may remain under `~/.hermes` when the manifest
  identifies them as canonical shared files.

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

All three agents may:

- Read the Neon V2 skill and references.
- Run local validation and synchronization scripts.
- Read the public Band Sheet and public calendar.
- Use configured APIs and authenticated services.
- Create local venue folders, receipts, queues, and drafts.
- Perform approved Calendar, AgentMail, WordPress, and Band Sheet actions.

Protected actions still require Mike's explicit approval:

- Create, edit, or delete a Google Calendar event.
- Send venue-facing email.
- Publish Band Sheet changes.
- Update WordPress.
- Share venue portal files.
- Change booking or pay terms.
- Mark a payment complete.

## Compatibility Test

Run for each agent:

```bash
python3 scripts/agent_compatibility_check.py --agent codex
python3 scripts/agent_compatibility_check.py --agent claude
python3 scripts/agent_compatibility_check.py --agent hermes
```

The Club Babaloo fixture is always test data. It must produce a local plan and
must report every protected write as `false`.

An agent is a full operator only when its receipt returns `status: success`.
