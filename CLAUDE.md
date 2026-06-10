# Claude Entry Point

Load `SKILL.md` as the Neon V2 operational authority.

Load `AGENT_COMPATIBILITY.md` before using credentials, APIs, or protected
actions. Run:

```bash
python3 scripts/agent_compatibility_check.py --agent claude
```

Claude is a full operator when the compatibility receipt succeeds. Do not
expose secret values or maintain Claude-only credentials.
