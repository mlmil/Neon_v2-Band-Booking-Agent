from dataclasses import dataclass


@dataclass(frozen=True)
class MemberProfile:
    member_id: str
    name: str
    role: str
    default_origin_city: str
    alternate_origin_cities: list[str]
    standard_arrival_minutes: int
    pa_load_in_arrival_minutes: int
    live_location_required: bool
