# Neon V2 README and Infographics Design

## Purpose

Replace the minimal repository README with a detailed, public-facing explanation of Neon V2: an agentic operations system built for Neon Blonde, a five-member band based in Ventura, California, that performs throughout the Southern California coast.

The README should explain the system to musicians, venue partners, developers, and people interested in practical agentic workflows without exposing credentials, private operational data, or machine-specific configuration.

## Positioning

Neon V2 is the operational agent for Neon Blonde. It connects booking intake, schedule verification, rehearsals, band communication, public gig information, show-day coordination, and post-gig administration into one supervised workflow.

The system is not an autonomous booking authority. It reasons, monitors, verifies, drafts, alerts, and coordinates. Mike retains approval over bookings, public publishing, venue-facing communication, rates, payments, and other protected actions.

## README Structure

1. Branded hero with the main Neon V2 infographic.
2. Concise project summary and band context.
3. Explanation of the operational problem Neon V2 solves.
4. Full agentic workflow from inquiry through post-gig closeout.
5. Core capabilities:
   - booking and email intake
   - availability verification
   - rehearsal coordination
   - Band Sheet and public-show verification
   - venue folders and operational records
   - Telegram and GroupMe communication
   - dashboard and health monitoring
   - Gig Copilot
   - payout, tip-jar, and Venmo closeout
6. Dedicated Gig Copilot section with its infographic.
7. Human approval and safety boundaries.
8. Architecture and source-of-truth overview.
9. Repository map.
10. Local setup and validation overview without secret values.
11. Current project status and intended audience.

## Main Infographic

### Message

Show Neon V2 as a coastal band-operations command center that connects the complete gig lifecycle:

`Booking inquiry → intake and verification → availability and rehearsal → confirmed gig operations → Gig Copilot → post-gig closeout`

### Visual Direction

- Sleek dark background.
- Electric pink, cyan, sunset orange, and restrained off-white.
- Subtle Southern California coastal references without becoming a tourism poster.
- Modern operational diagram with clear flow and minimal text.
- Five-member band identity represented without generating identifiable portraits.
- Wide GitHub-friendly composition.

### Required Labels

- Booking Intake
- Availability Verification
- Rehearsals
- Band Sheet
- Human Approval
- Gig Copilot
- Website Verification
- Post-Gig Closeout
- Neon V2
- Ventura, California

## Gig Copilot Infographic

### Message

Gig Copilot is Neon Blonde's day-of-show coordination system. It helps five working musicians reach the venue safely and on time while reducing the need to continuously monitor their phones.

### Operational Flow

`Live location sharing → traffic and weather monitoring → shared ETAs → delay and change alerts → coordinated arrival → setup and showtime`

### Location-Sharing Policy

- Location sharing is consent-based.
- It is activated for the gig-day operational window.
- Members can see shared location, travel progress, and ETA.
- Members can add manual updates when traffic, work, or other delays occur.
- The system alerts when arrival or setup timing is at risk.
- Tracking ends when the gig-day workflow closes.
- The README must not claim that features are currently deployed if they remain planned or partially implemented.

### Required Labels

- Gig Copilot
- Live Location Sharing
- Traffic
- Weather
- Shared ETA Board
- Band Check-Ins
- Risk Alerts
- Safe Arrival
- Setup
- Showtime

## Accuracy Rules

- Describe Neon Blonde as a five-member band.
- Describe the band as based in Ventura, California, and performing up and down the Southern California coast.
- Distinguish implemented, supervised, and planned capabilities.
- Do not imply Google Calendar write access.
- Do not imply unrestricted autonomous email, website, Band Sheet, booking, rate, or payment changes.
- Do not include credential paths, tokens, private chat IDs, member home addresses, or private calendar URLs.
- Keep live location sharing framed as temporary, consensual gig-day coordination.

## Deliverables

- Revised root `README.md`.
- Main repository infographic under `docs/images/`.
- Separate Gig Copilot infographic under `docs/images/`.
- Both images embedded in the README with useful alt text.
- Verification of Markdown links, image paths, spelling, factual claims, and repository status.

## Publishing

Add the README and infographics as a focused follow-up commit on the existing `codex/telegram-booking-watcher` branch and update draft pull request #1.
