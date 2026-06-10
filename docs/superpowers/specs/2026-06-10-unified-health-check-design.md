# Unified Health Check Design

## Goal

Provide one read-only Neon V2 command that runs the AgentMail, Band Sheet,
website, and dashboard-data checks and returns one machine-readable receipt.

## Behavior

- Run every lane even when an earlier lane fails.
- Reuse each existing check's Python function rather than parsing command output.
- Convert unexpected exceptions into a blocked lane receipt.
- Mark the overall result `success` only when every lane succeeds.
- Never send email, write Calendar data, publish the Band Sheet, update
  WordPress, complete payments, or start the dashboard server.

## Lanes

1. `agentmail`: verifies API authentication and access to the Neon Blonde inbox.
2. `bandsheet`: compares the public Google Calendar with the published Band Sheet.
3. `website`: compares public WordPress shows with the published Band Sheet.
4. `dashboard`: verifies dashboard files and validates that Post-Gig queue data
   can be loaded from local CSV files.

## Output

The command prints JSON containing:

- overall `status`
- overall `code`
- timestamp
- one result per lane
- counts of successful and blocked lanes
- `protected_writes_performed: 0`
- `credential_values_exposed: false`

Exit code is `0` for full success and `1` when one or more lanes are blocked.

## Failure Isolation

Each lane runs inside its own exception boundary. A network, authentication,
parsing, or local-file failure blocks only that lane. The remaining lanes still
run and appear in the final receipt.

## Verification

Unit tests inject deterministic lane functions so they do not depend on live
network services. A final supervised live run verifies the real integrations.
