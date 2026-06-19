# Neon V2 Supervised Pilot Audit

**Observation Window:** June 10, 2026, ~14:57 to 16:14 PDT (approx. 1 hour 15 mins).
*Note: A full 24 hours has not yet elapsed. This audit remains open.*

## 1. Monitor Run Counts & Success/Failures
- **Gmail Intake**: 5 runs | 5 successes | 0 failures
- **GroupMe Sync**: 4 runs | 2 successes | 2 failures
- **Health Check**: 1 run | 1 success | 0 failures (within log window; 2 receipts present)
- **Venue Sync**: 1 run | 1 success | 0 failures

## 2. Gmail Intake Analysis
- **Actionable Messages**: 0 new actionable emails in the observation window (33 total new since last check).
- **Receipts Created**: 14 total receipts found in `data/intake/receipts/`.
- **Duplicates Detected** (3 threads):
  - Wedding Contract Sept 6 (May 12 & Jun 10)
  - Neon Blonde Band Booking (May 18 & Jun 5)
  - Oxnard Band Entertainment Bark Lead (Jun 10 & Jul 25)
- **Likely False Positives**:
  - WordPress promotional/update emails (e.g., "AI builds it", "Build your website in no time")
  - Make.com marketing ("AMA with Make product team")
  - Bark.com leads/spam ("Contact this client in Ventura... for free")

## 3. GroupMe Sync Data
- **New Message Count by Group** (Total: 1,273):
  - Neon Blonde: 1,010
  - Blackstar: 168
  - Potentials: 79
  - Neon Blonde UPCOMING: 14
  - Harrys: 2
- **Sync Failures**:
  - `15:22` - `[ERROR] Drive_A is unavailable. Halting sync.`
  - `15:57` - `ERROR: GroupMe API returned 401 for /groups: Unauthorized`

## 4. Health-Lane Status
Based on latest receipt (`1781130128.json`):
- **Successful Lanes**: 5
- **Blocked Lanes**: 0
- **Needs-Review Lanes**: 0
- **Overall Status**: `ALL_HEALTH_CHECKS_OK`

## 5. Venue Folders & Digests
- **Created/Changed**: 0
- The venue sync processed 14 gigs successfully, but all folders and local model digests were already up to date (`created_venue_folder: false`, `created_gig_folder: false`).

## 6. LM Studio Availability
- LM Studio is consistently available across both health receipts.
- Responding at `http://127.0.0.1:1234` with model `gemma-4-e2b-it`.
- 59 models recognized.

## 7. Safety & Credentials
- **Credential Exposure**: None (`credential_values_exposed: false`).
- **Protected Writes**: None (`protected_writes_performed: 0`).
- **Unexpected Side Effects**: None observed. The system safely performed read-only actions and generated local data.

## 8. Blockers & Recommended Fixes
1. **Observation Timeframe**: 24 hours have not elapsed.
   - *Fix*: Keep the pilot running to capture overnight cron jobs and a full diurnal cycle.
2. **Gmail False Positives**: Promotional emails from WordPress, Make.com, and Bark are creating receipts.
   - *Fix*: Update `scripts/intake_email_parser.py` or email sweep filter patterns to automatically discard domains/subjects from `bark.com`, `wordpress.com`, and `make.com`.
3. **GroupMe Volume Dependency**: Sync failed when `Drive_A` was unavailable.
   - *Fix*: Add a volume check before attempting sync, or fail gracefully.
4. **GroupMe Auth Drops**: API returned a 401 Unauthorized.
   - *Fix*: Ensure the token is stable and not expiring/rate-limited.

## 9. Go/No-Go Recommendation
**NO-GO for dashboard connection.**

**Reasoning**:
1. The 24-hour observation period is incomplete.
2. Connecting Gmail intake right now will flood the dashboard approval queue with marketing spam/false positives from WordPress and Bark.
3. GroupMe sync has reliability issues (Drive_A dependency and 401 errors) that need to be patched to ensure continuous synchronization.
