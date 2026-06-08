# OAuth Token Failure Modes

Two distinct failure modes produce different error messages and require different fixes.

## Failure Mode A: `invalid_client` — Stale Client Secret

**Problem**: The OAuth token file (`~/.hermes/neon_oauth_token.json`) embeds the `client_secret` that was active when the token was first authorized. If the Google Cloud project's OAuth client secret is rotated or regenerated, the embedded secret becomes invalid.

**Error**: `google.auth.exceptions.RefreshError: ('invalid_client: The provided client secret is invalid.', ...)`

**Root cause**: The token file caches `client_secret` at creation time. Rotating the secret in Google Cloud Console invalidates all existing tokens that reference the old secret. The VADER drive (`/Volumes/VADER/Projects/Neon_Blonde/Google WorkSpace Client Secret/`) holds the current client secret JSON but may not be mounted during cron/automation runs.

**Fix**: Edit the token file's `client_secret` field directly to the new value:
1. Find the current client secret JSON. Check these locations (first found wins):
   - `/Volumes/VADER/Projects/Neon_Blonde/Google WorkSpace Client Secret/` (these filenames include version numbers like `client_secret_3_...`)
   - `~/.hermes/neon_client_secret.json` — may be from the `neon-blonde-calendar` project (different secret than `stellar-vista-486501-s2`)
   - `~/.hermes/client_secret.json`
   - `~/Google Workspace Configs/Neon Blonde/google_client_secret_NB.json` or `google_client_secret.json`
2. Extract the `client_secret` value from `installed.client_secret` or `web.client_secret` in the JSON.
3. Patch the token file at `~/.hermes/neon_oauth_token.json` — change `"client_secret": "old_value"` to the new value.
4. The refresh token and scopes remain valid; only the embedded secret changed. No browser re-auth needed.

**⚠️ Multiple project distinction**: The `stellar-vista-486501-s2` project client secrets use the old secret (`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` as of May 2026). The `neon-blonde-calendar` project has a different secret (`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` as of May 2026). If the token's embedded `client_id` starts with the same project prefix (657887685429-...), match against the correct project's secret.

## Failure Mode B: `invalid_grant` — Expired or Revoked Refresh Token

**Error**: `google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.', ...)`

**Meaning**: The refresh token itself has been invalidated — the user revoked the app's access in their Google account security settings, or the token is too old.

**Symptom**: Token loads from disk fine (client_id, client_secret, scopes all present), `creds.expired` is True, but `creds.refresh()` fails with `invalid_grant`. Trying alternate client_secrets from other Google Cloud projects produces `invalid_client` errors (mismatched secret), confirming the original secret is still correct. **Swapping the client_secret does NOT fix this.**

**Root cause**: The user revoked the "Neon Blonde Calendar" or "stellar-vista-486501-s2" app access from their Google Account security settings (myaccount.google.com → Security → Third-party apps with account access), or the refresh token was issued more than 6 months ago without re-consent. Google periodically invalidates long-lived refresh tokens.

**Fix**: A fresh OAuth authorization is required.
1. Run `scripts/generate_oob_auth_url.py` in this skill to produce an OOB (out-of-band) authorization URL.
2. Share the URL with Mike. He opens it in an **incognito browser** signed into **neonblondevc@gmail.com** (not his personal account).
3. The consent screen prompts for calendar read/write access. Mike approves it and receives a code.
4. He pastes the code back. The script exchanges it for a new token with a fresh refresh_token.
5. The new token is saved to `~/.hermes/neon_oauth_token.json`.

The `prompt=consent` flag in the script forces fresh login regardless of saved sessions, ensuring a new refresh token is issued.

## How to distinguish A from B

| Signal | `invalid_client` (A) | `invalid_grant` (B) |
|---|---|---|
| Error string | `invalid_client: The provided client secret is invalid` | `invalid_grant: Token has been expired or revoked` |
| Root cause | Client secret was rotated | Refresh token was revoked/expired |
| Fix | Edit client_secret in token file | Re-authorize via OOB URL |
| Can you patch the file? | Yes | No — file edit won't help |

**Decision rule**: Check the error string first. `invalid_client` → patch the secret. `invalid_grant` → re-authorize. Do not try to swap client_secrets when the error is `invalid_grant` — it's a different problem.

## Fallback when calendar is unavailable

When OAuth is broken (either mode A or B) and VADER isn't mounted, you can still run a complete briefing using just the Band Sheet website:

- **Confirmed gigs**: Full list with dates, times, and venues from the Band Sheet JSON endpoint
- **Member outs**: The Band Sheet's member-out section (but note end dates may be truncated by 1 day vs. calendar — adjust accordingly)
- **Open days**: The Band Sheet's "free_weekends" section (but remember these don't cross-check member availability)
- **Email**: IMAP with app password still works (no OAuth dependency)
- **Venue folders**: Google Drive syncs to local filesystem — still accessible via `~/Library/CloudStorage/GoogleDrive-neonblondevc@gmail.com/My Drive/Venues/`
- **What you lose**: Calendar-specific events like tentative gigs, rehearsal entries, and member-out events marked "probably" or "maybe" that the Band Sheet doesn't capture
- **Freshground rehearsals**: The iCal feed at `freshgroundrecords@gmail.com` is still accessible (no OAuth) — check for rehearsals independently

**Operational rule**: Do NOT report the auth error to Mike. Say what you could access and what you couldn't, concisely.
