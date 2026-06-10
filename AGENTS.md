# Codex Entry Point

Load `SKILL.md` as the Neon V2 operational authority.

Load `AGENT_COMPATIBILITY.md` before using credentials, APIs, or protected
actions. Run:

```bash
python3 scripts/agent_compatibility_check.py --agent codex
```

Do not expose secret values. A missing shared credential is a blocker, not a
reason to create a Codex-only copy.
