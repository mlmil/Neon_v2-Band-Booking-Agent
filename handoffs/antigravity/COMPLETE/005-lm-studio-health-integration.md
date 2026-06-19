# Task 005: LM Studio Health Integration

## Objective

Add LM Studio as a read-only Neon V2 health lane and connect its real status to
the dashboard Local Model panel.

LM Studio runs at:

```text
http://127.0.0.1:1234
```

Use:

```text
GET /v1/models
```

Do not run inference as part of the health check.

## Required Reading

1. `SKILL.md`
2. `AGENT_COMPATIBILITY.md`
3. `handoffs/antigravity/README.md`
4. `scripts/neon_health_check.py`
5. `tests/test_neon_health_check.py`
6. `scripts/local_venue_folder_sync.py`
7. `tests/test_local_venue_folder_sync.py`
8. `scripts/dashboard_server.py`
9. `tests/test_dashboard_server.py`
10. `dashboard/components/app.jsx`
11. `dashboard/components/panels.jsx`
12. `dashboard/data/data.js`
13. `design_handoff_neon_v2_dashboard/README.md`

## Existing Work To Preserve

Do not modify:

- Task 004 Gmail intake files
- GroupMe workflow files
- Scout Agent files
- credential files or manifests
- Calendar/public-feed behavior
- existing LM Studio digest generation behavior
- unrelated untracked directories

## Architecture

Create a small read-only LM Studio health adapter, preferably:

```text
scripts/lm_studio_health_check.py
tests/test_lm_studio_health_check.py
```

The adapter should:

1. Request `GET http://127.0.0.1:1234/v1/models`.
2. Use a short health timeout, separate from the 120-second inference timeout.
3. Parse OpenAI-compatible model-list responses.
4. Check whether the configured Neon model is present.
5. Never submit a prompt or trigger generation.
6. Never expose request headers, environment values, or model file paths beyond
   the public model ID returned by LM Studio.

Configuration:

```text
NEON_LOCAL_MODEL_URL=http://127.0.0.1:1234
NEON_LOCAL_MODEL=gemma-4-e2b-it
```

Defaults must match the existing local venue digest client.

## Status Contract

Healthy:

```json
{
  "status": "success",
  "code": "LM_STUDIO_OK",
  "server": "http://127.0.0.1:1234",
  "configured_model": "gemma-4-e2b-it",
  "configured_model_available": true,
  "model_count": 1
}
```

Server unavailable:

```json
{
  "status": "blocked",
  "code": "LM_STUDIO_UNAVAILABLE"
}
```

Server online but configured model missing:

```json
{
  "status": "needs_review",
  "code": "LM_STUDIO_MODEL_MISSING",
  "configured_model": "gemma-4-e2b-it",
  "configured_model_available": false
}
```

Malformed response:

```json
{
  "status": "blocked",
  "code": "LM_STUDIO_RESPONSE_INVALID"
}
```

## Unified Health Check

Add an `lm_studio` lane to `scripts/neon_health_check.py`.

Aggregation rules:

- `success` remains healthy.
- `needs_review` must not be counted as success.
- A failed LM Studio lane must not stop any other lane.
- The consolidated receipt must still state zero protected writes.
- No secret-shaped field may appear.

## Dashboard Integration

Expose the real LM Studio status through the local dashboard API.

Preferred approach:

- Add a read-only endpoint such as `GET /api/health`.
- Return the consolidated health receipt or a redacted dashboard projection.
- On dashboard load, replace only `window.NEON_DATA.local_model_digest` with
  the live LM Studio result.
- Keep all unrelated mock dashboard lanes unchanged.

Map statuses:

```text
success      -> success
needs_review -> needs_review
blocked      -> blocked
```

Dashboard fields:

```text
status
title: LM Studio
model
last_ok
message
pending_digests
```

`pending_digests` may remain the existing local mock/list value unless a real
read-only source already exists. Do not invent filesystem scanning outside this
task.

If the dashboard server is unavailable, preserve the existing mock status and
show a non-destructive error toast.

## TDD Requirements

Write failing tests before implementation.

Required adapter tests:

1. Uses `GET /v1/models`.
2. Correctly identifies the configured model.
3. Returns `needs_review` when the configured model is absent.
4. Returns `blocked` when LM Studio is offline.
5. Returns `blocked` for malformed JSON/schema.
6. Does not submit prompts or call `/v1/chat/completions`.
7. Receipt contains no credential-shaped fields.

Required unified health tests:

8. LM Studio lane runs with all existing lanes.
9. LM Studio failure is isolated.
10. `needs_review` makes overall status non-success.

Required dashboard tests:

11. Health endpoint returns redacted LM Studio status.
12. Dashboard projection maps all three statuses.
13. No dashboard write endpoint is introduced.
14. Existing Post-Gig endpoints continue working.

## Safety Boundary

Allowed:

- Read `GET /v1/models`.
- Edit local code, tests, dashboard files, and docs.
- Run the local dashboard server.
- Open the local dashboard for visual verification.

Not approved:

- Run model inference during health checks or verification.
- Write venue digests.
- Modify Gmail, GroupMe, Calendar, Drive, Contacts, AgentMail, Band Sheet,
  WordPress, or payments.
- Read or change credentials.
- Commit or push.

## Verification

Run:

```bash
python3 -m unittest tests/test_lm_studio_health_check.py
python3 -m unittest tests/test_neon_health_check.py
python3 -m unittest tests/test_dashboard_server.py
python3 scripts/lm_studio_health_check.py
python3 scripts/neon_health_check.py
git diff --check
```

Run the local dashboard server and confirm:

- Local Model panel displays LM Studio.
- The configured model is shown.
- The panel status matches the health endpoint.
- Existing Post-Gig data still renders.
- Browser console has no new errors.

Stop the server after verification.

## Completion Report

Move this file to `handoffs/antigravity/REVIEW/` and append:

```text
Status: complete
Files changed: scripts/lm_studio_health_check.py, scripts/neon_health_check.py, scripts/dashboard_server.py, dashboard/components/app.jsx, tests/test_lm_studio_health_check.py, tests/test_neon_health_check.py, tests/test_dashboard_server.py
LM Studio URL: http://127.0.0.1:1234
Configured model: gemma-4-e2b-it
Models endpoint verified: yes (/v1/models)
Inference requests performed: 0
Unified health lane verified: yes (lm_studio lane incorporated, needs_review correctly prevents ALL_HEALTH_CHECKS_OK)
Dashboard health endpoint: yes (GET /api/health)
Dashboard Local Model panel verified: yes (dynamically reads from live health endpoint and merges pending_digests)
Existing Post-Gig API preserved: yes
Browser console errors: None
Commands run: 6
Tests passed: 24/24 (for specific task modules)
Tests failed: 0
Protected writes performed: 0
Credential values exposed: no
Unrelated existing changes preserved: yes
Blockers: None
Recommended next step: Proceed to the next task in the queue.
```

## Acceptance Criteria

- LM Studio is represented by a read-only health lane.
- Health checking uses `/v1/models`, never inference.
- Configured-model availability is reported accurately.
- LM Studio failures remain isolated from other health lanes.
- Dashboard Local Model status comes from the live health endpoint.
- Existing Post-Gig behavior remains intact.
- No protected write occurs.
- No credential value is exposed.
- Unrelated changes remain untouched.

## Codex Review

Status: ACCEPTED

Verified:

- LM Studio health uses `GET /v1/models` only.
- No inference request is part of the health lane.
- Configured model `gemma-4-e2b-it` is available.
- Unified health now reports five successful lanes.
- Dashboard health projection maps success, needs-review, and blocked states.
- Existing Post-Gig tests remain green.
- 34 focused tests passed.
- Live LM Studio and consolidated health checks passed.
- No protected write occurred.
