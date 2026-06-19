#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agentmail_health_check import run_health_check as agentmail_check
from scripts.bandsheet_verification_report import run_live_check as bandsheet_check
from scripts.dashboard_server import get_post_gig_data
from scripts.lm_studio_health_check import run_health_check as lm_studio_check
from scripts.website_verification_report import run_live_check as website_check


PACIFIC = ZoneInfo("America/Los_Angeles")
Check = Callable[[], dict]
SENSITIVE_FIELDS = {
    "api_key",
    "authorization",
    "key",
    "password",
    "secret",
    "token",
}


def _redact_sensitive_fields(value):
    if isinstance(value, dict):
        return {
            key: _redact_sensitive_fields(item)
            for key, item in value.items()
            if key.lower() not in SENSITIVE_FIELDS
        }
    if isinstance(value, list):
        return [_redact_sensitive_fields(item) for item in value]
    return value


def dashboard_health_check(
    *,
    dashboard_dir: Path = REPO_ROOT / "dashboard",
    queue_path: Path = REPO_ROOT / "data" / "post_gig" / "queue.csv",
    payouts_path: Path = Path("/Volumes/VADER/Manifold/Neon_Blonde/Administrative/PAYOUT TRACKING SPREADSHEET/neon-blonde_Payouts 2026.csv"),
) -> dict:
    required_files = [
        dashboard_dir / "index.html",
        dashboard_dir / "components" / "app.jsx",
        dashboard_dir / "components" / "panels.jsx",
    ]
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        return {
            "status": "blocked",
            "code": "DASHBOARD_FILES_MISSING",
            "missing_files": missing,
        }
    if not queue_path.is_file():
        return {
            "status": "blocked",
            "code": "POST_GIG_QUEUE_MISSING",
            "queue_path": str(queue_path),
        }

    items = get_post_gig_data(queue_path, payouts_path)
    return {
        "status": "success",
        "code": "DASHBOARD_DATA_OK",
        "active_post_gig_items": len(items),
        "payout_ledger_present": payouts_path.is_file(),
    }


def default_checks() -> dict[str, Check]:
    return {
        "agentmail": agentmail_check,
        "bandsheet": bandsheet_check,
        "website": website_check,
        "dashboard": dashboard_health_check,
        "lm_studio": lm_studio_check,
    }


def run_health_checks(checks: dict[str, Check] | None = None) -> dict:
    lane_results = {}
    for name, check in (checks or default_checks()).items():
        try:
            result = check()
            if not isinstance(result, dict):
                raise TypeError("Health check must return a dictionary.")
            lane_results[name] = _redact_sensitive_fields(result)
        except Exception as exc:
            lane_results[name] = {
                "status": "blocked",
                "code": "HEALTH_CHECK_EXCEPTION",
                "error": str(exc),
                "exception_type": type(exc).__name__,
            }

    successful = sum(
        result.get("status") == "success" for result in lane_results.values()
    )
    blocked = sum(
        result.get("status") == "blocked" for result in lane_results.values()
    )
    needs_review = len(lane_results) - successful - blocked

    if blocked > 0:
        overall_status = "blocked"
        overall_code = "HEALTH_CHECKS_BLOCKED"
    elif needs_review > 0:
        overall_status = "needs_review"
        overall_code = "HEALTH_CHECKS_NEED_REVIEW"
    else:
        overall_status = "success"
        overall_code = "ALL_HEALTH_CHECKS_OK"

    return {
        "status": overall_status,
        "code": overall_code,
        "checked_at": datetime.now(PACIFIC).isoformat(),
        "successful_lanes": successful,
        "blocked_lanes": blocked,
        "needs_review_lanes": needs_review,
        "lanes": lane_results,
        "protected_writes_performed": 0,
        "credential_values_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all read-only Neon V2 health-check lanes."
    )
    parser.parse_args()
    result = run_health_checks()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
