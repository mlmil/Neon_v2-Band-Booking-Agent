---
name: telegram-outbound-messaging
description: Safely prepare, authorize, send, and verify Telegram messages on a user's behalf, with exact destination checks and honest failure reporting.
---

# Telegram Outbound Messaging

Use this class skill whenever a user asks the agent to post, send, or announce something in Telegram. This is an outbound-action workflow, distinct from passive Telegram monitoring.

## Workflow

1. **Resolve the destination.** Identify the stable chat ID or otherwise verified chat identity. Never infer that a generic connected label such as `Home` is the authorized Neon Blonde group. The allowlisted Neon Blonde group is `-1004424634571`; other destinations require independent identity confirmation.
2. **Resolve the final text.** Preserve the user's wording unless they request editing. For relative dates such as “tomorrow,” retain the user's wording unless an exact date is necessary to avoid ambiguity.
3. **Check authorization.** Sending a Telegram message on the user's behalf is a protected external action. Require explicit approval of the intended destination and final text. Do not infer approval from silence, a prior unrelated approval, or a generic request whose audience remains unclear.
4. **Use configured credentials safely.** Send only through the active profile gateway or an approved Bot API path. Never print, expose, or include bot tokens in logs or user-facing output.
5. **Verify delivery.** Report success only after the gateway/API confirms success and provides a receipt such as a message ID and destination. An attempted call is not evidence of delivery.
6. **Report failures honestly.** If the send is blocked, times out, or returns an error, say that it was not sent and provide the exact unsent message. Do not claim or imply delivery.

## Safety and privacy

- Do not send sensitive payment, access, address, or private-contact details to an unverified group.
- If the user chooses a generic channel after being told its identity is unconfirmed, preserve that uncertainty in the execution record and do not relabel it as the band group.
- Avoid silently rewriting money-related statements; wording should remain attributable to the user.

## References

See `references/outbound-gate.md` for the compact decision sequence and failure-reporting template.
