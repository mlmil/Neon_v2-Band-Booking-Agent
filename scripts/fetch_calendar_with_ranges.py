#!/usr/bin/env python3
"""
Fetch Neon Blonde calendar events with full date ranges.

The standard mcpl calendar_list_events API only returns start dates.
This script uses the Google Calendar Python library to fetch the FULL
event duration (start to end dates), which is essential for identifying
multi-day out-of-office blocks, vacations, etc.

Usage:
    python3 fetch_calendar_with_ranges.py

Output:
    Prints all "Out" and "Absence" events with their full date ranges
"""

import json
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
SECRETS_FILE = '/Users/studio_hub/Google Workspace Configs/Neon Blonde/google_client_secret_NB.json'
TOKEN_FILE = '/Users/studio_hub/.hermes/google_token.json'
CALENDAR_ID = 'neonblondevc@gmail.com'

def fetch_calendar_events_with_ranges():
    """Fetch calendar events with full start/end date information."""

    try:
        # Load token and secrets
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        with open(SECRETS_FILE) as f:
            secrets = json.load(f)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure both files exist:")
        print(f"  {TOKEN_FILE}")
        print(f"  {SECRETS_FILE}")
        sys.exit(1)

    # Merge credentials with token
    creds_info = {
        **token_data,
        'client_id': secrets.get('installed', {}).get('client_id'),
        'client_secret': secrets.get('installed', {}).get('client_secret'),
    }

    # Create credentials and refresh if needed
    creds = Credentials.from_authorized_user_info(creds_info)
    if creds.expired:
        creds.refresh(Request())

    # Build Google Calendar API service
    service = build('calendar', 'v3', credentials=creds)

    # Fetch events with full details
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        maxResults=200,
        singleEvents=True,
        fields='items(summary,start,end)'
    ).execute()

    return events_result.get('items', [])

def filter_out_events(events):
    """Filter for out-of-office and absence events, return with date ranges."""
    out_events = []

    for event in sorted(events, key=lambda x: x.get('start', {}).get('date') or x.get('start', {}).get('dateTime', '')):
        summary = event.get('summary', '')

        # Filter for out/absence events
        if 'Out' not in summary and 'out' not in summary and 'Absence' not in summary:
            continue

        # Extract start and end dates
        start = event.get('start', {})
        end = event.get('end', {})

        start_date = start.get('date') or start.get('dateTime', 'N/A').split('T')[0]
        end_date = end.get('date') or end.get('dateTime', 'N/A').split('T')[0]

        out_events.append({
            'summary': summary,
            'start': start_date,
            'end': end_date
        })

    return out_events

def format_date_range(start, end):
    """Format a date range for display."""
    if start == end:
        return start
    else:
        return f"{start} to {end}"

def main():
    print("Fetching Neon Blonde calendar events with full date ranges...\n")

    try:
        events = fetch_calendar_events_with_ranges()
        out_events = filter_out_events(events)

        if not out_events:
            print("No out-of-office events found.")
            return

        print(f"Found {len(out_events)} out-of-office event(s):\n")
        for event in out_events:
            date_range = format_date_range(event['start'], event['end'])
            print(f"{event['summary']}: {date_range}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
