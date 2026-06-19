import json
import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen

from telegram_bot.config import (
    BANDSHEET_JSON_URL,
    BANDSHEET_STALE_AFTER_DAYS,
    HTTP_TIMEOUT_SECONDS,
)
from telegram_bot.models import (
    BandSheetBookedGig,
    BandSheetSnapshot,
    BandSheetSource,
    ProviderWarning,
    ProviderWarningCode,
)

GIG_PATTERN = re.compile(
    r"^(?P<day>[A-Z]{3})\s+(?P<date>\d{1,2}-\d{1,2}-\d{4})\s+@(?P<time>[^-]+)-\s*(?P<venue>.+?)"
    r"(?:,\s*(?P<city>.+))?$"
)
PACIFIC_SUFFIX_PATTERN = re.compile(r"\s+P(?:DT|ST|T)$")
PACIFIC_TZ = timezone(-timedelta(hours=7))


class BandSheetProviderError(RuntimeError):
    """Base error for BandSheet provider failures."""


class BandSheetSchemaError(BandSheetProviderError):
    """Raised when the BandSheet payload cannot be parsed safely."""


class BandSheetFetchError(BandSheetProviderError):
    """Raised when the BandSheet payload cannot be fetched."""


class BandSheetFreshnessError(BandSheetProviderError):
    """Raised when the BandSheet payload is too stale for the requested mode."""


class BandSheetSnapshotProvider:
    def __init__(
        self,
        *,
        now: datetime | None = None,
        fail_on_stale: bool = False,
        source_url: str = BANDSHEET_JSON_URL,
        fetcher: Callable[[str], object] | None = None,
    ) -> None:
        self._now = now or datetime.now(UTC)
        self._fail_on_stale = fail_on_stale
        self._source_url = source_url
        self._fetcher = fetcher or self._fetch_json

    def load_snapshot(self) -> BandSheetSnapshot:
        try:
            payload = self._fetcher(self._source_url)
        except BandSheetProviderError:
            raise
        except Exception as exc:
            raise BandSheetFetchError(f"Failed to fetch BandSheet data from {self._source_url}") from exc

        return self.parse_payload(payload)

    def parse_payload(self, payload: object) -> BandSheetSnapshot:
        if not isinstance(payload, dict):
            raise BandSheetSchemaError("BandSheet payload must be a JSON object")

        updated_raw = payload.get("updated")
        if not isinstance(updated_raw, str):
            raise BandSheetSchemaError("BandSheet payload is missing a valid 'updated' field")
        updated_at = self._parse_updated_at(updated_raw)

        booked_gigs = self._require_string_list(payload, "booked_gigs")
        free_weekends = self._require_string_list(payload, "free_weekends")
        members_out = self._require_string_list(payload, "members_out")
        this_week = self._require_string_list(payload, "this_week")

        freshness_days = (self._now.date() - updated_at.date()).days
        is_stale = freshness_days > BANDSHEET_STALE_AFTER_DAYS
        warnings: list[ProviderWarning] = []
        if is_stale:
            warning = ProviderWarning(
                code=ProviderWarningCode.STALE_SOURCE,
                message=(
                    f"BandSheet data is {freshness_days} days old and should not be trusted for routing "
                    "without manual verification."
                ),
                blocking=True,
            )
            if self._fail_on_stale:
                raise BandSheetFreshnessError(warning.message)
            warnings.append(warning)

        source = BandSheetSource(
            source_url=self._source_url,
            fetched_at=self._now,
            updated_at=updated_at,
            freshness_days=freshness_days,
            is_stale=is_stale,
        )
        parsed_gigs = [self._parse_booked_gig(entry) for entry in booked_gigs]

        return BandSheetSnapshot(
            source=source,
            booked_gigs=parsed_gigs,
            free_weekends=free_weekends,
            members_out=members_out,
            this_week=this_week,
            warnings=warnings,
        )

    @staticmethod
    def _require_string_list(payload: dict[str, object], key: str) -> list[str]:
        value = payload.get(key)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise BandSheetSchemaError(f"BandSheet field '{key}' must be a list of strings")
        return value

    @staticmethod
    def _parse_booked_gig(summary: str) -> BandSheetBookedGig:
        normalized = summary.replace("—", "-")
        match = GIG_PATTERN.match(normalized)
        if not match:
            return BandSheetBookedGig(
                summary=summary,
                date=None,
                start_time=None,
                venue_name=None,
                city=None,
            )

        return BandSheetBookedGig(
            summary=summary,
            date=match.group("date"),
            start_time=match.group("time").strip(),
            venue_name=match.group("venue").strip(),
            city=match.group("city").strip() if match.group("city") else None,
        )

    @staticmethod
    def _parse_updated_at(updated_raw: str) -> datetime:
        try:
            return datetime.strptime(updated_raw, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            pass

        pacific_stamp = PACIFIC_SUFFIX_PATTERN.sub("", updated_raw)
        try:
            naive = datetime.strptime(pacific_stamp, "%B %d, %Y @ %I:%M %p")
        except ValueError as exc:
            raise BandSheetSchemaError(
                "BandSheet 'updated' field must be YYYY-MM-DD or 'Month DD, YYYY @ HH:MM AM/PM PT'"
            ) from exc

        return naive.replace(tzinfo=PACIFIC_TZ).astimezone(UTC)

    @staticmethod
    def _fetch_json(source_url: str) -> object:
        try:
            with urlopen(source_url, timeout=HTTP_TIMEOUT_SECONDS) as response:
                return json.load(response)
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BandSheetFetchError(f"Failed to fetch BandSheet data from {source_url}") from exc
