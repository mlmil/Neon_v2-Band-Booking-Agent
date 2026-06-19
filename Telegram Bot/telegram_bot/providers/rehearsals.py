import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Callable
from urllib.request import urlopen

FRESHGROUND_ICAL_URL = "https://calendar.google.com/calendar/ical/freshgroundrecords%40gmail.com/public/basic.ics"
PACIFIC_TZ = timezone(timedelta(hours=-7))


class FreshgroundRehearsalProvider:
    def __init__(
        self,
        *,
        now: datetime | None = None,
        source_url: str = FRESHGROUND_ICAL_URL,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        self._now = now or datetime.now(UTC)
        self._source_url = source_url
        self._fetcher = fetcher or self._fetch_ical

    def upcoming(self, *, limit: int = 5) -> list[str]:
        data = self._fetcher(self._source_url)
        rehearsals: list[tuple[datetime, str]] = []
        for event in data.split("BEGIN:VEVENT")[1:]:
            summary = self._line_value(event, "SUMMARY")
            dtstart = self._line_value(event, "DTSTART")
            if not summary or not dtstart or "neon" not in summary.lower():
                continue
            starts_at = self._parse_dtstart(dtstart)
            if starts_at < self._now.astimezone(PACIFIC_TZ):
                continue
            rehearsals.append((starts_at, f"{starts_at.strftime('%a %-m-%-d')} @ {starts_at.strftime('%-I:%M%p').lower()} - {summary}"))
        rehearsals.sort(key=lambda item: item[0])
        return [summary for _, summary in rehearsals[:limit]]

    @staticmethod
    def _line_value(event: str, name: str) -> str | None:
        for line in event.splitlines():
            if line.startswith(name):
                return line.split(":", 1)[1].strip()
        return None

    @staticmethod
    def _parse_dtstart(value: str) -> datetime:
        match = re.match(r"(\d{4})(\d{2})(\d{2})T?(\d{2})?(\d{2})?(\d{2})?(Z)?", value)
        if not match:
            raise ValueError(f"Unsupported DTSTART: {value}")
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        hour, minute = int(match.group(4) or 0), int(match.group(5) or 0)
        if match.group(7):
            return datetime(year, month, day, hour, minute, tzinfo=UTC).astimezone(PACIFIC_TZ)
        return datetime(year, month, day, hour, minute, tzinfo=PACIFIC_TZ)

    @staticmethod
    def _fetch_ical(source_url: str) -> str:
        with urlopen(source_url, timeout=10) as response:
            return response.read().decode("utf-8")
