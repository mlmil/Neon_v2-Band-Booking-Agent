#!/usr/bin/env python3
"""Fetch Neon Blonde calendar for the current week via OAuth."""
import json, os, sys
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_FILE = Path.home() / '.hermes' / 'neon_oauth_token.json'
CLIENT_SECRET = '/Users/studio_hub/tools-registry/mcps/google_workspace_mcp/client_secret.json'
CALENDAR_ID = 'neonblondevc@gmail.com'

def get_creds():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return creds

today = date.today()
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=7)

creds = get_creds()
service = build('calendar', 'v3', credentials=creds)

events_result = service.events().list(
    calendarId=CALENDAR_ID,
    timeMin=datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
    timeMax=datetime.combine(week_end, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
    singleEvents=True,
    orderBy='startTime',
    fields='items(summary,start,end)',
    maxResults=250,
).execute()

events = events_result.get('items', [])
print(f"Week: {week_start.strftime('%a %b %-d')} — {week_end.strftime('%a %b %-d')}\n")

if not events:
    print("No events this week — every day is open for rehearsal.")
else:
    conflicts = defaultdict(list)
    for e in events:
        s = e.get('start', {})
        end = e.get('end', {})
        day = s.get('date') or s.get('dateTime', '').split('T')[0]
        end_day = end.get('date') or end.get('dateTime', '').split('T')[0]
        summary = e.get('summary', '(no title)')
        conflicts[day].append((summary, end_day))
        print(f"  {day} → {end_day}  {summary}")

    print()

    # Determine open days — ANY calendar event blocks the day
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    open_days = []
    for d in week_days:
        key = d.isoformat()
        if key not in conflicts:
            open_days.append(d)

    print("OPEN FOR REHEARSAL:")
    if open_days:
        for d in sorted(open_days, key=lambda d: ({4:0,5:1,6:2}.get(d.weekday(),3), d)):
            print(f"  - {d.strftime('%a %b %-d')}")
    else:
        print("  No days available this week.")
