# WordPress Show Sync

Use this when Neon V2 needs to update the public Neon Blonde website schedule.

## Core Decision

Do not embed the Band Sheet on the public website.

The Band Sheet is for band members and family. The website should receive only public show data.

## Source Flow

```text
Google Calendar confirmed gig
  -> Neon V2 public show parser
  -> WordPress REST API
  -> public Show post
```

## API Target

The public show cards use the custom WordPress post type:

```text
POST /wp-json/wp/v2/show
POST /wp-json/wp/v2/show/{id}
```

The Events Calendar endpoint exists but is not the current front-page card source:

```text
/wp-json/tribe/events/v1/events
```

That endpoint returned zero upcoming events during discovery, while `wp/v2/show` contained the visible public show posts.

## Auth Note

Use a WordPress Application Password with Basic Auth.

The site is behind Cloudflare. Plain script requests can be blocked with Cloudflare error `1010`. Include a normal User-Agent header such as:

```text
User-Agent: NeonV2 Website Sync
```

Verified safe test:

- Created draft `show` post through API.
- Read draft back.
- Deleted draft.
- No public post was published.

Working script:

```text
scripts/wordpress_show_sync.py
```

Dry-run example:

```bash
python3 scripts/wordpress_show_sync.py \
  --venue "Cruisery" \
  --city "Santa Barbara" \
  --start "2026-06-12T21:00:00" \
  --show-year-term-id 18 \
  --featured-media-id 483 \
  --menu-order 11
```

Live smoke-test pattern:

```bash
NEON_WP_USERNAME="..." NEON_WP_APP_PASSWORD="..." \
python3 scripts/wordpress_show_sync.py \
  --venue "Neon V2 API Smoke Test" \
  --city "Ventura" \
  --start "2026-12-05T20:00:00" \
  --show-year-term-id 18 \
  --featured-media-id 483 \
  --menu-order 99 \
  --create-draft \
  --delete-after-read
```

The smoke-test creates a draft, reads it back, and deletes it.

## Public Show Fields

Observed REST fields on existing `show` posts:

- `title`
- `slug`
- `status`
- `featured_media`
- `show_year`
- `menu_order`

Example existing post:

```text
ID: 660
Title: June 12 Cruisery
Type: show
Featured media: 483
Show year: 18 (2026)
Menu order: 11
```

The time/city card line is not clearly exposed in REST yet. Before production sync, inspect the WordPress Show editor or theme/page-builder source to identify where those fields live.

## Public Website Verification

Use this checker to compare the published Band Sheet against the public WordPress show posts:

```bash
python3 scripts/website_verification_report.py
```

Current scope:

- Compares future public shows by date + venue.
- Uses `User-Agent: NeonV2 Website Sync` for the WordPress API.
- Ignores test venues such as `Club Babaloo` / `Club Bobaloo`.
- Allows private-party Band Sheet names to appear publicly as `Private Gig`, `Private Show`, or `Private Party`.
- Does not yet verify city/time, because those fields are not clearly exposed by the current WordPress REST response.

## Venue Logo / Featured Image

Venue Agent can own public-safe venue media:

1. Known venue: reuse the approved logo from WordPress media or the venue folder.
2. New venue: create a `needs_logo` task and ask Mike before using a newly found public logo.
3. Private party/wedding: use Neon Blonde fallback logo unless Mike provides a public image.
4. Test venue: never upload to WordPress.
5. No logo found: use Neon Blonde fallback logo.

WordPress media upload endpoint:

```text
POST /wp-json/wp/v2/media
```

Then attach image to show post:

```json
{
  "featured_media": 483
}
```

Local logo scout:

```text
scripts/venue_logo_scout.py
```

Official URL example:

```bash
python3 scripts/venue_logo_scout.py \
  --venue "Leashless Brewing" \
  --city "Ventura" \
  --url "https://leashlessbrewing.com"
```

Behavior:

- Discovers `apple-touch-icon`, OpenGraph image, Twitter image, and favicon candidates from the official page.
- Prefers higher-quality official logo/social images over browser favicons.
- Downloads the selected candidate locally.
- Writes a receipt with source URL, candidate URL, local path, and approval status.
- Does not upload to WordPress by default.

The next approval-gated step is uploading an approved local logo to WordPress media and using the returned media ID as `featured_media`.

Media upload smoke-test pattern:

```bash
NEON_WP_USERNAME="..." NEON_WP_APP_PASSWORD="..." \
python3 scripts/wordpress_show_sync.py \
  --venue "Logo Upload Test" \
  --city "Ventura" \
  --start "2026-12-05T20:00:00" \
  --show-year-term-id 18 \
  --upload-media /path/to/approved-logo.png \
  --media-title "Venue Logo" \
  --media-alt-text "Venue logo" \
  --delete-media-after-read
```

Verified safe test:

- Uploaded a Leashless Brewing logo scout file to WordPress media.
- Read the media item back.
- Deleted the media item.
- No public show post was created or changed.

## Protected Write

Publishing or updating WordPress public show posts is a protected write.

Default safe behavior:

- create draft
- read back
- show receipt to Mike
- only publish/update existing public post after Mike approval
