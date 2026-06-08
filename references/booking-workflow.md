# Neon Blonde Booking Workflow

## Overview

Neon Blonde uses a **two-phase booking model** to allow planning and scheduling flexibility throughout the year:
- **Spring/Summer Booking Phase**: Book gigs through June
- **Fall Booking Phase**: Start booking for fall in May

## Booking Phases

### Spring/Summer Phase (January-June)
- **When**: January through early May
- **What gets booked**: Gigs for February through June
- **Goal**: Lock in spring and early summer shows while fall is still uncertain

### Fall Booking Phase (May-October)
- **When**: Mid-May through September
- **What gets booked**: Gigs for September through December
- **Why now**: Better visibility on who's available, summer schedules becoming clearer

## Information Needed to Book a Gig

When a venue contacts Mike or someone about a potential gig, collect this information:

| Field | Required? | Notes |
|-------|-----------|-------|
| **Venue Name** | ✅ Yes | e.g., "Ventura Pier", "Sea Breeze Bar" |
| **Date** | ✅ Yes | Specific date or date range |
| **Day of Week** | ✅ Yes | Saturday, Friday, etc. |
| **Time** | ✅ Yes | Start time (e.g., "9pm", "10:30pm") |
| **Duration** | ✅ Yes | How long the set (e.g., "3 hours", "4 sets of 1 hour") |
| **End Time** | ⚠️ Better | Helps with planning around other events |
| **Contact** | ✅ Yes | Venue contact person + phone/email |
| **Pay** | ✅ Yes | Rate or flat fee + payment terms |
| **Setup Requirements** | ⚠️ Nice to have | Sound check time, parking, load-in notes |
| **Cancellation Policy** | ⚠️ Nice to have | How far in advance can either party cancel? |

## Process: Adding a Gig

**Mike asks**: "Add a gig: Saturday Feb 1, Ventura Pier, 9pm-Midnight, $400 flat fee"

**Steps**:
1. Collect all required information (see table above)
2. Check member availability (read the Neon Blonde 2026 calendar)
3. Alert if conflicts exist (e.g., "Tony is out Feb 1-3, so he'd miss this gig")
4. Add to Neon Blonde 2026 calendar
5. Update/regenerate The Band Sheet
6. Create the venue folder in Google Drive
7. Confirm: "Gig added for Saturday, February 1st at Ventura Pier"

### Venue folder rule
After adding a new venue gig, create a folder at:
`/Users/studio_hub/Library/CloudStorage/GoogleDrive-neonblondevc@gmail.com/My Drive/Venues`

Folder name:
`Venue Name - YYYY-MM-DD`

Example:
`Ventura Pier - 2026-02-01`

If the folder already exists, do not duplicate it.
Do this immediately after the calendar event is saved.

### Folder creation procedure
1. Confirm the gig date and venue name are final.
2. Normalize the folder name as `Venue Name - YYYY-MM-DD`.
3. Check whether the folder already exists in the Venues directory.
4. If it does not exist, create it.
5. If the venue name or date is still uncertain, do not create the folder yet.
6. Inside the folder, create a `notes` document and a 2048x2048 GIMP file named `Venue Name - YYYY-MM-DD`.
7. In the GIMP file, include template text on separate lines:
   - line 1: venue name
   - line 2: date in `SAT 5-10` format
   - line 3: time in `8-11` format

Use this as the operational rule:
- new venue gig confirmed = create folder
- tentative gig = wait
- duplicate folder = leave it alone

For the GIMP harness build details, see [gimp-harness-spec.md](gimp-harness-spec.md).

### Shell-safe creation example
After confirmation, create the folder with:

```bash
mkdir -p "/Users/studio_hub/Library/CloudStorage/GoogleDrive-neonblondevc@gmail.com/My Drive/Venues/Venue Name - YYYY-MM-DD"
```

Replace `Venue Name - YYYY-MM-DD` with the confirmed venue and date. Do not run this for tentative bookings.

### Venue package script
Use this script to create the folder, `notes` file, and GIMP template in one step:

```bash
scripts/create_venue_package.sh "Ventura Pier" "2026-02-01" "8-11"
```

Use `alt` as the fourth argument to generate the 1200x600 canvas preset instead of the default 2048x2048 canvas.
This script requires `cli-anything-gimp` to be installed and available on `PATH`.
If no canvas override is passed, the script auto-selects the 1200x600 preset for obvious daytime hints like `noon`, `12`, or `afternoon`; otherwise it uses 2048x2048.
The saved project file uses the venue/date name with a `.gimp-cli.json` extension.
The script also creates an `assets` folder inside the venue package.
The `assets` folder includes a short `README.md` placeholder.
The script normalizes venue names for filesystem safety before creating folders or filenames.

## Rehearsal Space

This is the band's rehearsal space.
The band rehearses here two or three times a month.
Fresh Ground Sound / Fresh Ground Records in Ventura is one example of this rehearsal-space pattern.
Mark Antaky runs Fresh Ground Sound.
Mark's contact details live in the shared contacts list.

Workflow:
1. Treat the location as a recurring rehearsal space, not a one-off gig venue.
2. Do not create a full venue package unless Mike explicitly asks for one.
3. Track rehearsal dates as rehearsal activity, not gigs.
4. When you need Fresh Ground contact details, pull them from the shared contacts list instead of guessing.

## Find Rehearsal Dates

When Mike asks for available rehearsal dates this week:
1. Check the calendar and member availability for the week.
2. Identify open rehearsal slots at the rehearsal space.
3. Use `scripts/find_rehearsal_dates.py` to generate the shortlist.
4. Present the available dates in plain language.
5. Flag questionable dates caused by weekday conflicts, member outs, or other bookings.
6. Do not email Mark yet. Wait for Mike to choose a date.
7. The shortlist script requires the Google Workspace config at `/Users/studio_hub/Google Workspace Configs/Neon Blonde` and the Hermes token at `/Users/studio_hub/.hermes/google_token.json`.
8. If the script fails, surface the exact cause:
   - missing config file
   - missing token file
   - invalid JSON
   - expired token that needs refresh
   - refresh blocked by network
   - Google Calendar client failure
   - calendar fetch failure

## Reserve Rehearsal Date

When Mike picks a rehearsal date and asks to reserve it:
1. Draft a friendly, brief email from the Neon Blonde email account to Mark Antaky.
2. Ask him to reserve the chosen rehearsal date.
3. Include the selected date and any relevant time window.
4. Send without an extra confirmation step once Mike asks.
5. Copy the sent email to `mikemllr77@gmail.com`.
6. If terminal email is available, use the email CLI workflow; otherwise prepare a Gmail draft.
7. If using Himalaya, draft from a pipe and send.
8. Record the sent email in the communication database so the rehearsal request stays searchable.
9. Use `scripts/log_sent_email.py` to write the sent-email record locally after sending.
10. If logging fails, say exactly why:
    - invalid database JSON
    - failed database write
    - missing or unreadable input

Suggested email format:
- To: Mark Antaky
- From: Neon Blonde Gmail account
- CC: `mikemllr77@gmail.com`
- Subject: `Rehearsal request: [DATE]`
- Body: short request to reserve the rehearsal space for Neon Blonde on the selected date

Suggested Himalaya template:
```bash
cat << 'EOF' | himalaya template send
From: neonblonde@example.com
To: mark@example.com
Cc: mikemllr77@gmail.com
Subject: Rehearsal request: [DATE]

Hi Mark,

Can you please reserve [DATE] for Neon Blonde at Fresh Ground Sound?

Thanks,
Neon Blonde
EOF
```

Suggested sent-email logging:
```bash
scripts/log_sent_email.py --to mark@example.com --cc mikemllr77@gmail.com --subject "Rehearsal request: [DATE]" --body "Can you please reserve [DATE] for Neon Blonde at Fresh Ground Sound?"
```

Error policy:
- Never hide a failure behind a generic "could not sync" or "something went wrong" message.
- State the exact file, token, JSON, network, or API failure and the next action to take.

## GroupMe Sync

Neon Blonde uses GroupMe for all band communication.

The workflow should:
1. Read `/Volumes/VADER/Neon_Blonde/GroupMeChats/messages` for JSON exports for each GroupMe message.
2. Update the communication database with new messages hourly.
3. Preserve timestamps, sender names, and any thread context available in the JSON.
4. Treat GroupMe as a source of truth for band communication and follow-up context.
5. Skip malformed or duplicate files and flag sync issues if needed.
6. Use `scripts/sync_groupme_messages.py` to refresh the local database.
7. Run the sync on launch and at least once every hour.

If the ingest folder path changes, ask Mike before syncing.

Suggested scheduler:
- hourly cron or launchd job
- also run immediately when the skill launches
- also run before morning check-ins and availability checks

Launch order:
1. Run `scripts/launch_neon_booking.sh`
2. Sync GroupMe
3. Continue with the requested booking or briefing task

Mount check:
- If `/Volumes/VADER/Neon_Blonde/GroupMeChats/messages` is missing, stop and tell Mike: `VADER is not mounted. Mount VADER and try again.`

## Availability Checking

### Before Confirming a Gig

Read the calendar and check:
1. **Are there existing gigs** that same day/night? (Possible conflicts with gear, energy, transportation)
2. **Is anyone blocked out** that day? (They'd miss the gig)
3. **Is it a multiple-member conflict?** (Affects which lineup is possible)

### What to Report

**If available**: "All clear for Saturday, Feb 1. Everyone available."

**If conflicts exist**: "Tony is out Feb 1-3, so he'd miss this. [other details if relevant]"

## Cancellation Process

If a gig needs to be cancelled:
1. Remove from the Neon Blonde 2026 calendar
2. Note why if known
3. Update/regenerate The Band Sheet
4. Inform the band via GroupMe: "Feb 1 Ventura Pier gig cancelled [reason if applicable]"

## Special Notes

### Two-Member Lineups
If only some members are available for a gig, note this clearly. Neon Blonde may do smaller lineups for some venues.

### Travel/Setup Conflicts
If a gig conflicts with travel time to another event that same day, flag it even if the member is technically "available".

### Payment Terms
Log payment information (some venues pay same-night, others invoice later). Track this for accounting/band finances.
