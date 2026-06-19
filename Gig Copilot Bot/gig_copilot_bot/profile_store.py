import json
from dataclasses import asdict
from pathlib import Path

from gig_copilot_bot.models import MemberProfile


class ProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load_profile(self, member_id: str) -> MemberProfile | None:
        payload = self._read_payload()
        profile = payload.get("profiles", {}).get(member_id)
        if not isinstance(profile, dict):
            return None
        return MemberProfile(
            member_id=str(profile["member_id"]),
            name=str(profile["name"]),
            role=str(profile["role"]),
            default_origin_city=str(profile["default_origin_city"]),
            alternate_origin_cities=list(profile["alternate_origin_cities"]),
            standard_arrival_minutes=int(profile["standard_arrival_minutes"]),
            pa_load_in_arrival_minutes=int(profile["pa_load_in_arrival_minutes"]),
            live_location_required=bool(profile["live_location_required"]),
        )

    def save_profile(self, profile: MemberProfile) -> None:
        payload = self._read_payload()
        profiles = payload.setdefault("profiles", {})
        profiles[profile.member_id] = asdict(profile)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _read_payload(self) -> dict[str, object]:
        if not self._path.exists():
            return {"profiles": {}}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"profiles": {}}
        return payload if isinstance(payload, dict) else {"profiles": {}}
