# Venue Template

Use this when a gig is confirmed and a venue package needs to be created.

## Folder Location

`~/Library/CloudStorage/GoogleDrive-neonblondevc@gmail.com/My Drive/Venues/`

## Folder Naming

Preferred new format:

`Venue Name - YYYY-MM-DD`

Existing folders may use:

`Venue Name - M D YYYY`

When checking for duplicates, search both formats before creating anything.

## Create Only When Confirmed

Create a venue package only when all are true:
- venue name is final
- gig date is final
- booking is confirmed
- Mike has not asked to hold off

Do not create venue folders for tentative gigs, member-out events, rehearsals, or general venue research.

## Package Contents

Use:

```bash
scripts/create_venue_package.sh "Venue Name" "YYYY-MM-DD" "8-11"
```

The package should include:
- venue folder
- notes file
- GIMP template file
- `assets/README.md`

Template text:
- line 1: venue name
- line 2: date in `SAT 5-10` format
- line 3: time in `8-11` format

Use the fourth script argument `alt` for the 1200x600 canvas preset when needed.
