from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class ProviderWarningCode(StrEnum):
    STALE_SOURCE = "stale_source"


@dataclass(frozen=True)
class RepoContext:
    repo_root: Path
    lane_root: Path
    lane_name: str


@dataclass(frozen=True)
class ProviderWarning:
    code: ProviderWarningCode
    message: str
    blocking: bool = False


@dataclass(frozen=True)
class BandSheetSource:
    source_url: str
    fetched_at: datetime
    updated_at: datetime
    freshness_days: int
    is_stale: bool


@dataclass(frozen=True)
class BandSheetBookedGig:
    summary: str
    date: str | None
    start_time: str | None
    venue_name: str | None
    city: str | None


@dataclass(frozen=True)
class BandSheetSnapshot:
    source: BandSheetSource
    booked_gigs: list[BandSheetBookedGig]
    free_weekends: list[str]
    members_out: list[str]
    this_week: list[str]
    warnings: list[ProviderWarning]
