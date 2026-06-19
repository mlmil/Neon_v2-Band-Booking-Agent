import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.post_gig_queue_sync import (
    QueueGig,
    build_queue_row,
    parse_calendar_queue_gigs,
    sync_queue,
)


PACIFIC = ZoneInfo("America/Los_Angeles")


class PostGigQueueSyncTests(unittest.TestCase):
    def test_future_gig_stays_scheduled_until_end_time(self):
        gig = QueueGig(
            gig_id="club-babaloo-2026-10-07",
            venue="Club Babaloo",
            city="Ventura",
            start_at="2026-10-07T19:00:00-07:00",
            end_at="2026-10-07T21:00:00-07:00",
        )

        row = build_queue_row(gig, now=datetime(2026, 10, 7, 20, 0, tzinfo=PACIFIC))

        self.assertEqual(row["queue_status"], "scheduled")
        self.assertEqual(row["next_step"], "Wait until the show ends.")

    def test_past_gig_activates_closeout(self):
        gig = QueueGig(
            gig_id="club-babaloo-2026-10-07",
            venue="Club Babaloo",
            city="Ventura",
            start_at="2026-10-07T19:00:00-07:00",
            end_at="2026-10-07T21:00:00-07:00",
        )

        row = build_queue_row(gig, now=datetime(2026, 10, 7, 21, 1, tzinfo=PACIFIC))

        self.assertEqual(row["queue_status"], "needs_closeout")
        self.assertIn("base pay", row["next_step"])
        self.assertIn("tip jar", row["next_step"])
        self.assertIn("Venmo", row["next_step"])

    def test_calendar_parser_uses_uid_and_pacific_start_and_end_times(self):
        ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:club-babaloo-test
DTSTART:20261008T020000Z
DTEND:20261008T040000Z
SUMMARY:Club Bobaloo
LOCATION:Ventura
END:VEVENT
END:VCALENDAR
"""

        gigs = parse_calendar_queue_gigs(ics)

        self.assertEqual(len(gigs), 1)
        self.assertEqual(gigs[0].gig_id, "club-babaloo-test")
        self.assertEqual(gigs[0].venue, "Club Babaloo")
        self.assertEqual(gigs[0].start_at, "2026-10-07T19:00:00-07:00")
        self.assertEqual(gigs[0].end_at, "2026-10-07T21:00:00-07:00")

    def test_sync_preserves_manual_closed_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "queue.csv"
            with queue_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "gig_id",
                        "venue",
                        "city",
                        "date",
                        "start_at",
                        "end_at",
                        "queue_status",
                        "next_step",
                        "created_at",
                        "updated_at",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "gig_id": "closed-gig",
                        "venue": "Tony's Pizza",
                        "city": "Ventura",
                        "date": "2026-06-01",
                        "start_at": "2026-06-01T19:00:00-07:00",
                        "end_at": "2026-06-01T21:00:00-07:00",
                        "queue_status": "closed",
                        "next_step": "No action.",
                        "created_at": "2026-06-01T21:01:00-07:00",
                        "updated_at": "2026-06-01T21:01:00-07:00",
                    }
                )
            gig = QueueGig(
                gig_id="closed-gig",
                venue="Tony's Pizza",
                city="Ventura",
                start_at="2026-06-01T19:00:00-07:00",
                end_at="2026-06-01T21:00:00-07:00",
            )

            sync_queue(
                [gig],
                queue_path,
                now=datetime(2026, 6, 9, 12, 0, tzinfo=PACIFIC),
            )

            with queue_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(rows[0]["queue_status"], "closed")
        self.assertEqual(rows[0]["next_step"], "No action.")

    def test_sync_is_idempotent_and_adds_new_gigs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "queue.csv"
            gig = QueueGig(
                gig_id="new-gig",
                venue="Leashless Brewing",
                city="Ventura",
                start_at="2026-07-18T18:00:00-07:00",
                end_at="2026-07-18T21:00:00-07:00",
            )
            now = datetime(2026, 6, 9, 12, 0, tzinfo=PACIFIC)

            sync_queue([gig], queue_path, now=now)
            receipt = sync_queue([gig], queue_path, now=now)

            with queue_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 1)
        self.assertEqual(receipt["created"], 0)
        self.assertEqual(receipt["updated"], 1)
        self.assertEqual(receipt["activated"], 0)

    def test_sync_counts_only_new_closeout_transitions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_path = Path(temp_dir) / "queue.csv"
            gig = QueueGig(
                gig_id="transition-gig",
                venue="Tony's Pizza",
                city="Ventura",
                start_at="2026-06-12T19:00:00-07:00",
                end_at="2026-06-12T21:00:00-07:00",
            )

            sync_queue(
                [gig],
                queue_path,
                now=datetime(2026, 6, 12, 20, 0, tzinfo=PACIFIC),
            )
            activated = sync_queue(
                [gig],
                queue_path,
                now=datetime(2026, 6, 12, 21, 1, tzinfo=PACIFIC),
            )
            repeated = sync_queue(
                [gig],
                queue_path,
                now=datetime(2026, 6, 12, 22, 0, tzinfo=PACIFIC),
            )

        self.assertEqual(activated["activated"], 1)
        self.assertEqual(repeated["activated"], 0)


if __name__ == "__main__":
    unittest.main()
