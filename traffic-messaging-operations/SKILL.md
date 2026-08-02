---
name: traffic-messaging-operations
description: Prepare, send, and verify same-day gig traffic updates to approved band members, with clear language, direct-instruction overrides, and honest Telegram delivery receipts.
---

# Traffic Messaging Operations

Use this class skill whenever a user asks to send traffic or departure updates to band members, whether the request comes from a scheduled monitor or a direct follow-up.

## Core workflow

1. Resolve the approved member destinations and the latest verified route estimates.
2. Use plain language in user-facing explanations. Say “send updates when traffic conditions change,” not “send only material updates.”
3. Distinguish the scheduled default from a direct instruction:
   - Scheduled default: compare against the stored baseline and send when traffic conditions change.
   - Direct user instruction: send the currently verified update immediately, even if the scheduled job would otherwise wait for a change or treat the scan as a baseline.
4. Never let a conditional automation gate silently override an explicit request to send.
5. Keep private origins and exact addresses out of group messages; member-specific route details may be sent privately to the relevant approved member.
6. Send through the configured Telegram bot/gateway only.
7. Verify every send using Telegram’s accepted response and message ID. Report Telegram acceptance separately from proof that the member read the message.

## Baseline handling

A first scan may establish a comparison baseline. If no member messages are sent, say explicitly: “This scan established the baseline, so no member updates were sent.” Do not describe that outcome as “no material change” without explaining what it means. If the user then asks for the updates, send the latest verified estimates immediately.

## Failure handling

- If a refresh succeeds but the scheduled job suppresses delivery, bypass the suppression for a direct user instruction and send the verified update directly.
- If a send fails, name the affected member(s), state that delivery was not verified, and preserve the exact unsent text for retry.
- Do not claim a member read the message merely because Telegram accepted it.
