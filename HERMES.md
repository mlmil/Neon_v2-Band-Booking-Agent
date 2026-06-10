# Hermes Entry Point

The canonical Hermes skill path is:

```text
/Users/studio_hub/.hermes/skills/Neon_v2
```

It must resolve to this repository. Load `SKILL.md` and
`AGENT_COMPATIBILITY.md`, then run:

```bash
python3 scripts/agent_compatibility_check.py --agent hermes
```

Hermes is a full operator when the compatibility receipt succeeds. Do not
expose secret values or maintain Hermes-only credentials outside the canonical
shared sources listed in `config/credential-manifest.json`.
