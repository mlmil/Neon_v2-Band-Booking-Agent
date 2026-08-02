---
name: gig-day-traffic-monitoring
description: Monitor same-day gig routes using an explicitly configured traffic source, compare member-specific route baselines, send only material private updates, and verify Telegram receipts without exposing private locations.
---

# Gig-Day Traffic Monitoring

Use this class skill for scheduled, same-day route monitoring when the user supplies a venue, arrival deadline, member origins, and an explicit traffic source such as configured Google Maps.

## Operating workflow

1. Confirm local date/time and stop if outside the requested day or travel window.
2. Resolve the exact venue in the configured traffic source. Preserve the user's supplied address as authoritative; record any harmless normalization and flag a genuine mismatch privately.
3. Query one driving route per member from the member's general origin area to the venue. Capture only displayed duration, distance, route, and traffic annotation. Never infer a route time from arithmetic or substitute another provider when the user requested Google Maps traffic.
4. Keep exact venue/member location data in private active-gig state keyed by gig ID and Telegram user ID. Never expose exact member locations in group messages.
5. On the first successful scan, establish a private baseline. A baseline is not itself a material change, so do not send member DMs solely because it is the first scan. Send Mike a concise private summary after every successful scan.
6. On later scans, compare each member's duration and traffic annotation against that member's stored baseline. Send a member DM only when traffic or safe-departure guidance materially changes for that member.
7. Do not claim a departure time was calculated unless an actual route estimate and an explicitly configured buffer support it. Never subtract a guessed buffer from a route estimate.
8. Update state only after route queries complete. Store each outbound receipt with destination and Telegram message ID. Do not use the scheduled job's final auto-delivery to Mike as a substitute for member DMs.

## Google Maps browser source

Use a driving directions URL for each origin and the normalized venue, e.g. `/maps/dir/<origin>/<venue>/data=!4m2!4m1!3e0`. Read the driving card, not transit/walking cards. Preserve traffic annotations such as `usual traffic`, `due to traffic conditions`, `avoids slowdown`, or displayed delays. A traffic-affected fastest route is evidence of current conditions, not automatically a safe-departure calculation.

## Telegram delivery

Use the active Co-Pilot gateway or Bot API path and approved Telegram IDs. For standalone Bot API calls, read `TELEGRAM_BOT_TOKEN` from the profile-local `.env` without printing it, call `sendMessage`, and verify `ok: true`, the expected destination, and `message_id`. Report delivery only from that receipt. Keep admin/errors private to Mike and never send routine route details to the band group.

## Reference

See `references/traffic-scan-runbook.md` for the reusable scan checklist and evidence/receipt format.

## Pitfalls

- Do not treat a first scan as a material change.
- Do not replace a user-specified address with a similarly named place.
- Do not invent route or departure times.
- Do not combine private member route details into a group message.
- Do not claim a member DM was sent when only the cron job's final Mike delivery succeeded.
