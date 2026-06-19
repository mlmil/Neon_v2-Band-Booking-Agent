#!/usr/bin/env python3
"""
Generate an OOB (out-of-band) Google OAuth authorization URL for the
Neon Blonde calendar.

Use this when the local server flow hangs (cron/automation) or when
the cached token (~/.hermes/neon_oauth_token.json) is stale and
needs fresh authorization.

USAGE:
    python3 generate_oob_auth_url.py

1. Opens a URL to print to stdout
2. User opens it in INCOGNITO/PRIVATE browser window
3. Signs in with neonblondevc@gmail.com
4. Approves the calendar read-only scope
5. Copies the code shown on the screen
6. Pastes it here to complete the flow

REQUIRES:
    pip3 install google-auth-oauthlib
    VADER drive mounted at /Volumes/VADER/
"""

import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']

# --- Locate client secret ---
secret_dir = "/Volumes/VADER/Projects/Neon_Blonde/Google WorkSpace Client Secret"
if not os.path.isdir(secret_dir):
    print(f"ERROR: VADER drive not mounted — can't find {secret_dir}", file=sys.stderr)
    sys.exit(1)

secrets = [f for f in os.listdir(secret_dir)
           if f.startswith("client_secret") and f.endswith(".json")]
if not secrets:
    print(f"ERROR: No client_secret JSON found in {secret_dir}", file=sys.stderr)
    sys.exit(1)

with open(os.path.join(secret_dir, secrets[0])) as f:
    client_config = json.load(f)

# --- Generate OOB auth URL ---
flow = InstalledAppFlow.from_client_config(
    client_config,
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)
auth_url, _ = flow.authorization_url(prompt='consent')

print("\n" + "=" * 70)
print("OPEN THIS URL IN AN INCOGNITO / PRIVATE BROWSER WINDOW")
print("=" * 70)
print()
print("Sign in with:  neonblondevc@gmail.com")
print()
print(auth_url)
print()
print("=" * 70)
print("After approving, you'll see a code on a white page.")
print("Copy that code and paste it back here.")
print("=" * 70)
