# WordPress Public Shows Widget

## Decision

Use WordPress as a public display layer for upcoming shows, but do not embed or expose the internal Band Sheet.

## Immediate Fix

Replace the current manually maintained shows/events section with the Custom HTML block in:

`templates/WORDPRESS_PUBLIC_SHOWS_WIDGET.html`

## Source Of Truth

```text
Google Calendar -> Band Sheet generator -> public filtered shows widget
```

WordPress should not become a second schedule database, and the website should not display the full Band Sheet.

## Privacy Boundary

The Band Sheet is for band members and family only. The public website can show:

- date
- venue/public event name
- city
- public start time

The public website must not show:

- member availability
- free weekends/open days
- internal admin notes
- payment or venue operations notes
- test venues such as Club Babaloo / Club Bobaloo

## Current WordPress Page

The public REST API shows:

- Page: `https://neonblonde.band/cal/`
- Page ID: `463`
- Title: `Band Calendar - Internal`
- Current content: Google Calendar iframe

## Current Publish Policy

WordPress API auth has been proven with Application Passwords and a normal User-Agent header. Publishing remains approval-gated.

Default safe behavior:

1. Create draft public `show` post through the API.
2. Read the draft back.
3. Show Mike the receipt.
4. Publish/update only after approval.

## Later Upgrade

The better long-term version is a native WordPress/Astro schedule component backed by a dedicated public JSON endpoint. That endpoint should be generated separately from the full Band Sheet JSON so public/private data boundaries are enforced before the browser ever sees the data.
