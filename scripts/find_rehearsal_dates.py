#!/usr/bin/env python3
"""
Find the best rehearsal dates for the current week.

This script uses the configured MCP Google server to scan the Neon Blonde
calendar for booked events and absence/out events, then prints a shortlist of
open rehearsal dates.
"""

import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import TransportError
from googleapiclient.discovery import build

CALENDAR_ID = "neonblondevc@gmail.com"
CONFIG_DIR = Path("/Users/studio_hub/Google Workspace Configs/Neon Blonde")
SECRETS_FILE = CONFIG_DIR / "google_client_secret_NB.json"
TOKEN_FILE = Path("/Users/studio_hub/.hermes/google_token.json")


def fail(message: str, code: int = 1):
    raise SystemExit(f"ERROR: {message}")


def load_credentials():
    try:
        with TOKEN_FILE.open("r", encoding="utf-8") as f:
            token_data = json.load(f)
        with SECRETS_FILE.open("r", encoding="utf-8") as f:
            secrets = json.load(f)
    except FileNotFoundError as e:
        fail(
            f"Missing Google auth file: {e.filename}. "
            f"Expected config at {SECRETS_FILE} and token at {TOKEN_FILE}."
        )
    except json.JSONDecodeError as e:
        fail(f"Invalid JSON in Google auth file {e.msg} at line {e.lineno}, column {e.colno}.")

    creds_info = {
        **token_data,
        "client_id": secrets.get("installed", {}).get("client_id"),
        "client_secret": secrets.get("installed", {}).get("client_secret"),
    }
    if not creds_info.get("client_id") or not creds_info.get("client_secret"):
        fail(
            f"Missing client_id or client_secret in {SECRETS_FILE}. "
            "Recreate the Neon Blonde Google Workspace config."
        )
    creds = Credentials.from_authorized_user_info(creds_info)
    if creds.expired:
        try:
            creds.refresh(Request())
        except TransportError as e:
            fail(
                "Google auth refresh failed while contacting Google. "
                "If the token is expired, refresh it in a networked environment and rerun."
            )
    return creds


def week_bounds(today: date):
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    return start, end


def fetch_events():
    try:
        service = build("calendar", "v3", credentials=load_credentials())
    except Exception as e:
        fail(f"Failed to create Google Calendar client: {e}")
    today = date.today()
    start, end = week_bounds(today)
    try:
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            timeMax=datetime.combine(end, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
            singleEvents=True,
            orderBy="startTime",
            fields="items(summary,start,end)",
            maxResults=250,
        ).execute()
    except Exception as e:
        fail(f"Failed to fetch calendar events for {CALENDAR_ID}: {e}")
    return events_result.get("items", [])


def build_day_map(events):
    day_map = defaultdict(list)
    for event in events:
        summary = (event.get("summary") or "").strip()
        start = event.get("start", {})
        day = start.get("date") or start.get("dateTime", "").split("T")[0]
        if not day:
            continue
        day_map[day].append(summary)
    return day_map


def is_conflict(summary: str) -> bool:
    s = summary.lower()
    return any(term in s for term in ("out", "absence", "vacation", "rehears", "gig", "show", "booked"))


def best_dates_for_week():
    events = fetch_events()
    day_map = build_day_map(events)

    today = date.today()
    start, _ = week_bounds(today)
    days = [start + timedelta(days=i) for i in range(7)]

    open_days = []
    for d in days:
        key = d.isoformat()
        summaries = day_map.get(key, [])
        if summaries and any(is_conflict(s) for s in summaries):
            continue
        if summaries:
            continue
        open_days.append(d)

    def rank(d: date):
        # Prefer Friday (4), Saturday (5), Sunday (6)
        preferred = {4: 0, 5: 1, 6: 2}.get(d.weekday(), 3)
        return (preferred, d)

    return sorted(open_days, key=rank)


def main():
    try:
        candidates = best_dates_for_week()
    except SystemExit:
        raise
    except Exception as e:
        fail(f"Unexpected rehearsal shortlist failure: {e}")

    print("Best rehearsal dates this week:\n")
    if not candidates:
        print("No open rehearsal dates found this week.")
        return

    for d in candidates:
        print(f"- {d.strftime('%a %b %-d')}")


if __name__ == "__main__":
    main()
