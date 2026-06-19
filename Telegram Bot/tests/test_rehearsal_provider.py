import unittest
from datetime import UTC, datetime

from telegram_bot.providers.rehearsals import FreshgroundRehearsalProvider


class FreshgroundRehearsalProviderTests(unittest.TestCase):
    def test_parses_upcoming_neon_rehearsals_from_ical(self) -> None:
        ical = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20260717T020000Z
DTEND:20260717T050000Z
SUMMARY:- 10 Neon Blond
END:VEVENT
BEGIN:VEVENT
DTSTART:20260718T180000Z
DTEND:20260718T200000Z
SUMMARY:Someone Else
END:VEVENT
END:VCALENDAR
"""
        provider = FreshgroundRehearsalProvider(
            now=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            fetcher=lambda _: ical,
        )

        rehearsals = provider.upcoming(limit=3)

        self.assertEqual(len(rehearsals), 1)
        self.assertEqual(rehearsals[0], "Thu 7-16 @ 7:00pm - - 10 Neon Blond")


if __name__ == "__main__":
    unittest.main()
