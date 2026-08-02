---
name: gmail-approved-reply-operations
description: Prepare, approve, send, thread, and verify Gmail replies on a user's behalf, preserving exact user corrections and requiring evidence-backed delivery verification.
---

# Gmail Approved Reply Operations

Use this class-level skill whenever a user asks to draft, revise, approve, send, or verify an email reply through Gmail SMTP/IMAP.

## Core contract

1. Identify the exact conversation, recipient, and source message before drafting.
2. Show the complete draft with recipient, subject, and body before sending.
3. Treat every user correction as a new exact draft revision. Preserve factual wording, pronouns, and possessives exactly as corrected; do not silently “smooth” them back to an earlier version.
4. Send only after explicit approval of the exact recipient, subject, and body. Approval is single-use; any later edit requires re-approval.
5. For replies, include the original `Message-ID` in `In-Reply-To` and `References` when available.
6. Send through the configured Gmail SMTP credentials without exposing secrets.
7. Verify the result in Gmail Sent Mail: match recipient and subject, fetch the full message, and compare its normalized plain-text body with the approved draft. SMTP success alone is not enough to claim verified delivery.
8. Report the actual SMTP result and verification evidence, including the generated message ID when available.

## Gmail IMAP verification fallback

Use a quoted mailbox name for names containing spaces or brackets, such as `"[Gmail]/Sent Mail"`. If compound IMAP search syntax is rejected, do not resend. Use `ALL` and scan a bounded set of recent Sent Mail headers, then fetch the matching full message and compare the body.

## Supporting reference

See `references/approved-gmail-reply-send.md` for the concise send/verification recipe and fallback details.

## Safety boundaries

Never infer approval from silence, an earlier draft, or a general request to “handle it” after the text has changed. Never claim the email was sent or verified without real SMTP/IMAP output.
