---
name: scheduled-gig-traffic-operations
description: Execute scheduled same-day gig traffic scans with explicit cron authorization, reliable Google Maps DOM extraction, material-change retries, and verified private Telegram delivery.
---

# Scheduled Gig Traffic Operations

Use this class skill for recurring or cron-triggered same-day route scans when the job prompt names the gig, members, origins, traffic source, and private messaging behavior.

## Operating contract

1. Treat the explicit scheduled prompt as authorization for the named operation and approved private destinations. Do not insert an interactive approval gate that blocks the requested run. Ad-hoc outbound messages outside the scheduled scope still require the normal approval workflow.
2. Query the configured traffic source for each member sequentially. Capture only provider-displayed driving duration, distance, route, and traffic annotation. Never derive route time arithmetically or substitute another provider.
3. Compare each member against a stored baseline and send only material member updates. A material change that was previously blocked or failed remains unresolved: retry the private alert while the condition remains material, even if the newest scan's delta is small.
4. Send the required operator summary after every successful scan. Verify every Telegram send with the expected destination and message ID; an attempted call is not delivery evidence.
5. Keep exact addresses and private origin details out of group messages and public reports. Do not expose admin or delivery errors to the group.
6. Do not calculate or claim a safe departure time without an actual route estimate and an explicitly configured contingency buffer.

## Google Maps browser reliability

The shared browser session is stateful. Never run concurrent navigations: they can race and leave an apparently empty page. Navigate one route at a time. If the accessibility snapshot is empty, inspect the rendered DOM with the browser console and read `document.body.innerText`. Accept a route only when the DOM contains the driving duration, distance, route, and traffic annotation. Retry sequentially when necessary.

## State and verification

Update active-gig state only after route collection completes. Preserve outbound receipts, unresolved-alert status, and the scan comparison timestamp. Verify the JSON/state file after writing. Stop when the configured travel window ends; do not continue a recurring job beyond its stated scope.

## Related guidance

Use `gig-day-traffic-monitoring` for the broader baseline and privacy contract, and `telegram-outbound-messaging` for general ad-hoc outbound safety. Session-specific browser and delivery notes are in `references/scan-lessons.md`.
