# How to Call Neon V2 Up

Start in the Neon V2 repository:

```bash
cd /Volumes/VADER/Manifold/Neon_Blonde/Repos/Neon_v2
```

## Hermes

Start an interactive Neon V2 session:

```bash
hermes chat --skills Neon_v2
```

Send one request:

```bash
hermes chat --skills Neon_v2 -q "Give me today's Neon Blonde operations briefing"
```

## Claude Code

Start Claude from the repository:

```bash
claude
```

Claude automatically reads `CLAUDE.md`. Then ask:

```text
Use Neon V2. Check the band schedule and operational alerts.
```

Send one request:

```bash
claude -p "Load SKILL.md and operate as Neon V2. Give me today's operations briefing."
```

## Gemini CLI

Start Gemini from the repository:

```bash
gemini --skip-trust
```

Then ask:

```text
Use Neon V2. Check the band schedule and operational alerts.
```

Send one request:

```bash
gemini --skip-trust -p "Load GEMINI.md and operate as Neon V2. Give me today's operations briefing."
```

## Useful Requests

```text
Use Neon V2. What does our schedule look like?
```

```text
Use Neon V2. Run the health check and report only failures.
```

```text
Use Neon V2. Check GroupMe, Gmail intake, Band Sheet, calendar, and website alignment.
```

```text
Use Neon V2. Draft the next operational actions, but do not send, publish, or modify anything.
```

## Operator Status

- Hermes: full Neon V2 operator within approval gates.
- Claude: full Neon V2 operator within approval gates.
- Gemini: full Neon V2 operator within approval gates when launched with `--skip-trust`.

Protected actions still require Mike's explicit approval:

- Send venue-facing email.
- Publish Band Sheet changes.
- Update WordPress.
- Share venue portal files.
- Change booking or pay terms.
- Mark a payment complete.
