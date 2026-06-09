# AgentMail Protocol

Use AgentMail for Neon Blonde operational communication when the request calls for agent-mediated email or band updates.

## Identity

The sender identity is **Neon V2** for operational assistant messages.

Do not sign as Mike.

Default sign-off:

```text
- Neon V2
```

Use `Neon Blonde` as the sender organization when writing to venues, rehearsal contacts, or booking agents.

## Approval Rule

Never auto-send booking commitments, gig confirmations, or availability promises without Mike's explicit approval.

If Mike explicitly asks to send a rehearsal reservation or operational update, send it without an extra confirmation step.

## Draft Handling

Pending drafts live at:

`~/.hermes/neon_pending_approvals.json`

Auto-clear obvious false positives from:
- `calendar-notification@google.com`
- `no-reply@accounts.google.com`
- `info@make.com`
- `noreply@*`
- empty session-log entries with no real reply content

Leave ambiguous or real booking drafts for Mike.

## Echo Loop Filter

When scanning IMAP, ignore AgentMail delivery echoes from `neon_blonde@agentmail.to` unless Mike specifically asks to inspect AgentMail delivery.

## Health Check

Before important AgentMail sends, run the read-only health check:

```bash
python3 scripts/agentmail_health_check.py
```

It verifies:

- `AGENTMAIL_API_KEY` is present without printing the key.
- The key can list AgentMail inboxes.
- `neon_blonde@agentmail.to` is visible.

Optional explicit send test:

```bash
python3 scripts/agentmail_health_check.py --send-test-to neonblondevc@gmail.com
```

Do not use the send test in scheduled automation unless Mike explicitly approves it.

## Send Wrapper

Use the send wrapper for operational AgentMail sends:

```bash
python3 scripts/agentmail_send.py \
  --to alfred@example.com \
  --cc neonblondevc@gmail.com \
  --subject "[Neon Blonde] Subject" \
  --text "Message body" \
  --fallback-gmail-draft
```

Behavior:

- Runs the AgentMail health check first.
- Sends from `neon_blonde@agentmail.to` by default.
- Appends `- Neon V2` if the message is not already signed.
- Returns a receipt with `message_id`, `thread_id`, recipients, and subject.
- Does not print the API key or full body in the receipt.
- If `--fallback-gmail-draft` is set and AgentMail is blocked, returns a `gmail_draft_required` payload that Codex can pass to the Gmail draft tool.

## Fallback

If AgentMail is unavailable, use the Neon Blonde Gmail/SMTP path from `smtp_config.json` or prepare a Gmail draft. State which path was used.
