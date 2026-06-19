import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from telegram_bot.models import ProviderWarningCode
from telegram_bot.providers.bandsheet import (
    BandSheetFetchError,
    BandSheetFreshnessError,
    BandSheetSchemaError,
    BandSheetSnapshotProvider,
)


class BandSheetProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        self.fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_builds_snapshot_from_valid_payload(self) -> None:
        provider = BandSheetSnapshotProvider(now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC))

        snapshot = provider.parse_payload(self.fixture_payload)

        self.assertEqual(snapshot.source.updated_at.isoformat(), "2026-06-14T00:00:00+00:00")
        self.assertFalse(snapshot.source.is_stale)
        self.assertEqual(len(snapshot.booked_gigs), 2)
        self.assertEqual(snapshot.booked_gigs[0].venue_name, "Santa Barbara Yacht Club")
        self.assertEqual(snapshot.booked_gigs[0].city, "Santa Barbara")
        self.assertEqual(snapshot.booked_gigs[0].start_time, "6PM")
        self.assertIsNone(snapshot.booked_gigs[1].city)
        self.assertEqual(snapshot.warnings, [])

    def test_marks_stale_payload_with_blocking_warning(self) -> None:
        provider = BandSheetSnapshotProvider(now=datetime(2026, 6, 20, 12, 0, tzinfo=UTC))

        snapshot = provider.parse_payload(self.fixture_payload)

        self.assertTrue(snapshot.source.is_stale)
        self.assertEqual(snapshot.warnings[0].code, ProviderWarningCode.STALE_SOURCE)
        self.assertTrue(snapshot.warnings[0].blocking)

    def test_raises_for_missing_updated_field(self) -> None:
        provider = BandSheetSnapshotProvider(now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC))
        payload = dict(self.fixture_payload)
        payload.pop("updated")

        with self.assertRaises(BandSheetSchemaError):
            provider.parse_payload(payload)

    def test_raises_for_bad_updated_format(self) -> None:
        provider = BandSheetSnapshotProvider(now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC))
        payload = dict(self.fixture_payload)
        payload["updated"] = "yesterday maybe"

        with self.assertRaises(BandSheetSchemaError):
            provider.parse_payload(payload)

    def test_raises_when_configured_to_fail_on_stale_source(self) -> None:
        provider = BandSheetSnapshotProvider(
            now=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
            fail_on_stale=True,
        )

        with self.assertRaises(BandSheetFreshnessError):
            provider.parse_payload(self.fixture_payload)

    def test_accepts_live_updated_timestamp_format(self) -> None:
        provider = BandSheetSnapshotProvider(now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC))
        payload = dict(self.fixture_payload)
        payload["updated"] = "June 15, 2026 @ 5:15 PM PT"

        snapshot = provider.parse_payload(payload)

        self.assertEqual(snapshot.source.updated_at.isoformat(), "2026-06-16T00:15:00+00:00")

    def test_load_snapshot_fetches_and_parses_payload(self) -> None:
        provider = BandSheetSnapshotProvider(
            now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
            fetcher=lambda _: self.fixture_payload,
        )

        snapshot = provider.load_snapshot()

        self.assertEqual(snapshot.booked_gigs[0].venue_name, "Santa Barbara Yacht Club")

    def test_load_snapshot_wraps_fetch_errors(self) -> None:
        provider = BandSheetSnapshotProvider(
            now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
            fetcher=lambda _: (_ for _ in ()).throw(TimeoutError("too slow")),
        )

        with self.assertRaises(BandSheetFetchError):
            provider.load_snapshot()


if __name__ == "__main__":
    unittest.main()
