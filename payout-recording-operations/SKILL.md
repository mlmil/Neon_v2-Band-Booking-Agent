---
name: payout-recording-operations
description: Record and verify Neon Blonde post-gig payments across base pay, tips, owner gratuities, and Venmo while resolving ambiguous additions safely.
---

# Payout Recording Operations

Use this class skill whenever Mike asks to record, correct, add, or reconcile a Neon Blonde post-gig payment.

## Workflow

1. Identify the venue, city, gig date, and payment components.
2. Separate base payment, tip-jar cash, owner/member tips, and Venmo. Do not silently collapse distinct sources in the explanation.
3. If an amount is described as “add,” “more,” or “from the owner” after a component already exists, clarify whether it is additional or a correction. Do not write until that distinction is resolved.
4. Upsert the existing ledger row keyed by venue and date; do not create a duplicate row for a correction or additional component.
5. Preserve the component breakdown in the ledger-supported fields and notes when multiple tip sources share one field.
6. Verify the written row and totals by rereading the ledger after the write.
7. Report the breakdown and total plainly, using dollars and the exact gig date.

## Ambiguity and arithmetic

- “$50 each” requires the member count before deriving a group tip total; never infer the count from an unrelated roster.
- If the user confirms an amount is additional, add it to the existing component and state the new component total before writing.
- If the user corrects a previously entered amount, replace it rather than accumulating it.
- Treat tip-jar and Venmo as separate components even when both are tips.

## Verification standard

A successful tool invocation is not enough. Confirm the receipt says `success` and `updated` or `created`, reread the exact venue/date row, and calculate/report the total from the verified fields. If the ledger schema combines owner tips with tip-jar cash, state that limitation and preserve the source distinction in notes.

## Plain-language reporting

Use “owner tip,” “tip-jar amount,” and “Venmo,” not vague labels such as “additional compensation.” If clarification was needed, briefly state whether the amount was added or replaced.
