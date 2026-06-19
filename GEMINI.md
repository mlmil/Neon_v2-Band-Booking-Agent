# Gemini Entry Point

Load `SKILL.md` as the Neon V2 operational authority.

Load `AGENT_COMPATIBILITY.md` before using credentials, APIs, or protected
actions. Run:

```bash
python3 scripts/agent_compatibility_check.py --agent gemini
```

Gemini is a full operator when the compatibility receipt succeeds. Do not
expose secret values or maintain Gemini-only credentials.

When launching Gemini CLI from this repository, use:

```bash
gemini --skip-trust
```

Without `--skip-trust`, Gemini may skip project instructions in this folder and
answer as a generic assistant instead of Neon V2.
