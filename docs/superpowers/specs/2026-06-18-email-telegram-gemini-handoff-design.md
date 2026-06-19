# Email to Telegram Gemini Handoff Design

## Goal

Turn each newly detected Neon Blonde booking email into a private Telegram alert that summarizes the request, checks the requested date against the public Neon calendar, and opens a stateful Gemini conversation for drafting a reply.

## Data Flow

1. The existing scheduled Gmail intake monitor reads the Neon Blonde inbox through read-only IMAP.
2. Existing keyword and sender rules classify actionable booking messages.
3. The monitor writes the existing local intake receipt and marks the message processed only after downstream handling succeeds.
4. A notifier parses the sender, requested date, city, event details, and pricing question.
5. Availability is checked twice against the public calendar. A date is described as open only when both checks agree and find no conflicting event or member-out entry.
6. The notifier sends a concise private Telegram message to Mike through `NeonBotstein_Bot`.
7. The full email context is saved as the active Gemini conversation email so Mike can continue naturally in Telegram.

## Telegram Message

The notification states who wrote, what they want, the requested date and location, and the availability result. If pricing is requested, Gemini asks Mike what rate to quote. It offers to draft a response but does not send one.

## Safety

- Gmail access remains read-only and uses `BODY.PEEK`.
- No Calendar writes are added.
- No venue-facing email is sent from the intake job.
- Gemini may draft and revise. Sending still requires Mike's explicit Telegram approval after the complete draft has been displayed.
- If calendar checks disagree or fail, the alert says availability is uncertain.
- If Telegram delivery fails, the message remains unprocessed so the scheduled job retries it.

## State

The existing processed-message file prevents duplicate notifications. The active email context is stored locally without credentials and is read by the existing Gemini agent before falling back to a fresh inbox search.

## Verification

Unit tests cover summary construction, pricing detection, two-pass availability, Telegram delivery, active-email persistence, retry behavior, and monitor integration. A bounded live check verifies credentials, bot identity, and scheduled service state without sending a synthetic venue email.
