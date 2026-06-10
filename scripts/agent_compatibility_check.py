#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.bandsheet_verification_report import PUBLIC_CALENDAR_ICS_URL
from scripts.venue_agent_tool import CalendarEvent, build_folder_plan


DEFAULT_MANIFEST = REPO_ROOT / "config" / "credential-manifest.json"
VALID_AGENTS = {"codex", "claude", "hermes"}


def _load_shared_environment(path: Path, environ: dict[str, str]) -> dict[str, str]:
    merged = dict(environ)
    if not path.is_file():
        return merged
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        merged.setdefault(name.strip(), value.strip().strip("'\""))
    return merged


def _source_available(source: dict, environ: dict[str, str]) -> bool:
    source_type = source.get("type")
    if source_type == "env":
        return bool(environ.get(source.get("name", "")))
    path = Path(source.get("path", ""))
    if not path.is_absolute():
        path = REPO_ROOT / path
    if source_type == "file":
        return path.is_file() and os.access(path, os.R_OK) and path.stat().st_size > 0
    if source_type == "json_key":
        if not path.is_file() or not os.access(path, os.R_OK):
            return False
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get(source.get("key", ""))
        except (OSError, json.JSONDecodeError):
            return False
        return bool(value)
    return False


def check_credential(credential: dict, environ: dict[str, str] | None = None) -> dict:
    environment = dict(os.environ if environ is None else environ)
    sources = credential.get("sources", [])
    available_sources = []
    for source in sources:
        if _source_available(source, environment):
            if source.get("type") == "env":
                available_sources.append({"type": "env", "name": source.get("name")})
            else:
                available_sources.append({"type": source.get("type"), "path": source.get("path")})
    return {
        "id": credential.get("id"),
        "required": bool(credential.get("required")),
        "status": "available" if available_sources else "missing",
        "available_sources": available_sources,
    }


def run_club_babaloo_fixture() -> dict:
    event = CalendarEvent(
        title="Club Bobaloo",
        location="Ventura",
        start="2026-10-07T19:00:00-07:00",
    )
    plan = build_folder_plan(event, Path("/tmp/neon-v2-agent-compatibility"))
    return {
        "status": plan["status"],
        "code": plan.get("code"),
        "is_test_venue": plan.get("is_test_venue", False),
        "warnings": plan.get("warnings", []),
        "protected_writes": {
            "calendar_updated": False,
            "bandsheet_published": False,
            "email_sent": False,
            "wordpress_updated": False,
            "payment_completed": False,
        },
    }


def _check_network() -> dict:
    request = urllib.request.Request(
        PUBLIC_CALENDAR_ICS_URL,
        headers={"User-Agent": "NeonV2 Agent Compatibility"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            available = response.status == 200 and bool(response.read(64))
    except Exception as exc:
        return {"status": "blocked", "reason": type(exc).__name__}
    return {"status": "available" if available else "blocked"}


def run_compatibility_check(
    *,
    agent: str,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    environ: dict[str, str] | None = None,
    run_network: bool = True,
) -> dict:
    normalized_agent = agent.strip().lower()
    if normalized_agent not in VALID_AGENTS:
        raise ValueError(f"unsupported agent: {agent}")
    manifest_file = Path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    environment = dict(os.environ if environ is None else environ)
    shared_env_value = manifest.get("shared_environment_file")
    if shared_env_value:
        environment = _load_shared_environment(Path(shared_env_value), environment)

    credentials = [
        check_credential(credential, environ=environment)
        for credential in manifest.get("credentials", [])
    ]
    missing_required = [
        credential["id"]
        for credential in credentials
        if credential["required"] and credential["status"] != "available"
    ]
    local_checks = {
        "skill": (REPO_ROOT / "SKILL.md").is_file(),
        "references": (REPO_ROOT / "references").is_dir(),
        "scripts": (REPO_ROOT / "scripts").is_dir(),
        "venues_root": Path("/Volumes/VADER/Manifold/Neon_Blonde/Venues").is_dir(),
    }
    network = _check_network() if run_network else {"status": "skipped"}
    fixture = run_club_babaloo_fixture()
    blocked = (
        bool(missing_required)
        or not all(local_checks.values())
        or fixture["status"] != "success"
        or network["status"] == "blocked"
    )
    return {
        "status": "blocked" if blocked else "success",
        "agent": normalized_agent,
        "policy": manifest.get("policy"),
        "local_checks": local_checks,
        "network": network,
        "credentials": credentials,
        "missing_required_credentials": missing_required,
        "club_babaloo": fixture,
        "secret_values_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Neon V2 agent compatibility.")
    parser.add_argument("--agent", required=True, choices=sorted(VALID_AGENTS))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        result = run_compatibility_check(
            agent=args.agent,
            manifest_path=args.manifest,
            run_network=not args.no_network,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "blocked", "agent": args.agent, "reason": str(exc)}

    output = json.dumps(result, indent=2)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if result.get("status") == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
