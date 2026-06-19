import json
import unittest
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.booking_watcher.models import ArchivedTelegramMessage, BookingSignal
from telegram_bot.booking_watcher.store import BookingWatcherStore
from telegram_bot.providers.bandsheet import BandSheetSnapshotProvider
from telegram_bot.providers.pending_drafts import PendingDraft
from telegram_bot.responder import build_reply


class ResponderTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.snapshot = BandSheetSnapshotProvider(now=datetime(2026, 6, 15, 12, 0, tzinfo=UTC)).parse_payload(payload)

    def test_help_reply_lists_commands_and_examples(self) -> None:
        reply = build_reply("/help", self.snapshot)

        self.assertIn("/gigs", reply)
        self.assertIn("/status", reply)
        self.assertIn("/members-out", reply)
        self.assertIn("/this-week", reply)
        self.assertIn("/free", reply)
        self.assertIn("/venue <name>", reply)
        self.assertIn("/rehearsals", reply)
        self.assertIn("/closeout", reply)
        self.assertIn("tip jar 200", reply)
        self.assertIn("Try: gigs", reply)
        self.assertIn("Try: venue leashless", reply)

    def test_gigs_reply_lists_upcoming_band_sheet_gigs(self) -> None:
        reply = build_reply("gigs", self.snapshot)

        self.assertIn("Upcoming gigs:", reply)
        self.assertIn("7-18-2026 @ 6PM - Santa Barbara Yacht Club (Santa Barbara)", reply)
        self.assertIn("8-14-2026 @ 8PM - Private Event", reply)

    def test_status_reply_reports_fresh_source(self) -> None:
        reply = build_reply("/status", self.snapshot)

        self.assertIn("BandSheet source is fresh", reply)
        self.assertIn("updated 2026-06-14", reply)

    def test_status_reply_blocks_stale_source(self) -> None:
        stale_snapshot = BandSheetSnapshotProvider(now=datetime(2026, 6, 20, 12, 0, tzinfo=UTC)).parse_payload(
            json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json").read_text())
        )

        reply = build_reply("/status", stale_snapshot)

        self.assertIn("BandSheet source is stale", reply)
        self.assertIn("manual verification", reply)

    def test_members_out_reply_lists_member_availability_notes(self) -> None:
        reply = build_reply("/members-out", self.snapshot)

        self.assertIn("Member availability notes:", reply)
        self.assertIn("- Alfred: SAT 6-27-2026 to THU 7-2-2026", reply)

    def test_this_week_reply_lists_this_week_notes(self) -> None:
        reply = build_reply("/this-week", self.snapshot)

        self.assertIn("This week:", reply)
        self.assertIn("DAVE OUT THURSDAY", reply)

    def test_free_reply_lists_open_days_with_freshness_context(self) -> None:
        reply = build_reply("/free", self.snapshot)

        self.assertIn("Band Sheet open dates:", reply)
        self.assertIn("- FRI June 19", reply)
        self.assertIn("Freshness: updated 2026-06-14", reply)

    def test_venue_reply_filters_upcoming_gigs_by_name(self) -> None:
        reply = build_reply("/venue yacht", self.snapshot)

        self.assertIn("Matching gigs for yacht:", reply)
        self.assertIn("7-18-2026 @ 6PM - Santa Barbara Yacht Club (Santa Barbara)", reply)
        self.assertNotIn("Private Event", reply)

    def test_venue_reply_handles_missing_query(self) -> None:
        reply = build_reply("/venue", self.snapshot)

        self.assertIn("Send /venue <name>", reply)

    def test_venue_reply_handles_no_matches(self) -> None:
        reply = build_reply("/venue dukes", self.snapshot)

        self.assertIn("No upcoming Band Sheet gigs found for dukes.", reply)

    def test_rehearsals_reply_lists_read_only_freshground_context(self) -> None:
        reply = build_reply("/rehearsals", self.snapshot, rehearsals=["Thu 7-16 @ 7:00pm - - 10 Neon Blond"])

        self.assertIn("Freshground rehearsals:", reply)
        self.assertIn("Thu 7-16 @ 7:00pm - - 10 Neon Blond", reply)

    def test_closeout_reply_lists_read_only_queue_summary(self) -> None:
        reply = build_reply("/closeout", self.snapshot, closeouts=["2026-06-06 - Tony's Pizza (Ventura): Ask Mike for pay."])

        self.assertIn("Post-gig closeout queue:", reply)
        self.assertIn("Tony's Pizza", reply)
        self.assertIn("read-only", reply)

    def test_show_me_the_draft_displays_pending_agentmail_draft(self) -> None:
        draft = PendingDraft(
            to=["rockstarentertainment805@gmail.com"],
            from_name="Phillip Thomas",
            subject="Re: New confirmed date",
            body="Hi Phillip,\n\nThanks for the update.",
        )

        reply = build_reply("/draft", self.snapshot, pending_drafts=[draft])

        self.assertIn("Pending AgentMail draft 1 of 1", reply)
        self.assertIn("Phillip Thomas", reply)
        self.assertIn("rockstarentertainment805@gmail.com", reply)
        self.assertIn("Re: New confirmed date", reply)
        self.assertIn("Thanks for the update", reply)
        self.assertIn("not sent", reply.lower())

    def test_agentmail_lists_pending_drafts(self) -> None:
        draft = PendingDraft(
            to=["rockstarentertainment805@gmail.com"],
            from_name="Phillip Thomas",
            subject="Re: New confirmed date",
            body="Body",
        )

        reply = build_reply("/agentmail", self.snapshot, pending_drafts=[draft])

        self.assertIn("1 AgentMail draft", reply)
        self.assertIn("Re: New confirmed date", reply)

    def test_show_email_from_philip_matches_sender_name(self) -> None:
        drafts = [
            PendingDraft(
                ["rockstarentertainment805@gmail.com"],
                "Phillip Thomas",
                "Re: New confirmed date",
                "Phillip body",
            ),
            PendingDraft(["someone@example.com"], "Other Person", "Other", "Other body"),
        ]

        reply = build_reply("/draft", self.snapshot, pending_drafts=drafts)

        self.assertIn("Phillip Thomas", reply)
        self.assertIn("Phillip body", reply)
        self.assertNotIn("Other body", reply)

    def test_natural_draft_language_goes_to_gemini_agent(self) -> None:
        calls: list[str] = []

        def answerer(question: str, snapshot: object) -> str:
            calls.append(question)
            return "Gemini conversation reply"

        reply = build_reply("Show me the email from Philip", self.snapshot, question_answerer=answerer)

        self.assertEqual(reply, "Gemini conversation reply")
        self.assertEqual(calls, ["Show me the email from Philip"])

    def test_flags_reply_lists_open_calendar_attention_items(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = self._store_with_cancellation(Path(temp_dir))

            reply = build_reply("/flags", self.snapshot, watcher_store=store)

        self.assertIn("Calendar attention queue:", reply)
        self.assertIn("flag-m1001-42", reply)
        self.assertIn("cancellation", reply)
        self.assertIn("June 27", reply)

    def test_reviewed_marks_queue_item_without_calendar_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = self._store_with_cancellation(Path(temp_dir))

            reply = build_reply("/reviewed flag-m1001-42", self.snapshot, watcher_store=store)

            self.assertIn("Marked reviewed", reply)
            self.assertIn("No Calendar changes were made", reply)
            self.assertEqual(store.list_open_items(), [])

    def test_dismiss_marks_queue_item_without_calendar_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = self._store_with_cancellation(Path(temp_dir))

            reply = build_reply("/dismiss flag-m1001-42", self.snapshot, watcher_store=store)

            self.assertIn("Dismissed", reply)
            self.assertIn("No Calendar changes were made", reply)
            self.assertEqual(store.list_open_items(), [])

    def test_watch_status_reports_store_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = BookingWatcherStore(Path(temp_dir))

            reply = build_reply("/watch-status", self.snapshot, watcher_store=store)

        self.assertIn("Telegram booking watcher:", reply)
        self.assertIn("configured", reply)

    def test_watcher_commands_report_unconfigured_store(self) -> None:
        reply = build_reply("/flags", self.snapshot)

        self.assertIn("Telegram booking watcher is not configured", reply)

    def test_unknown_reply_stays_inside_milestone_scope(self) -> None:
        reply = build_reply("can we book next Friday?", self.snapshot)

        self.assertIn("I can only answer read-only BandSheet questions", reply)
        self.assertIn("/help", reply)

    def test_unknown_reply_uses_read_only_question_answerer_when_available(self) -> None:
        calls: list[tuple[str, object]] = []

        def answerer(question: str, snapshot: object) -> str:
            calls.append((question, snapshot))
            return "The next gig is Santa Barbara Yacht Club."

        reply = build_reply("what is the next gig?", self.snapshot, question_answerer=answerer)

        self.assertEqual(reply, "The next gig is Santa Barbara Yacht Club.")
        self.assertEqual(calls, [("what is the next gig?", self.snapshot)])

    def test_unknown_reply_handles_question_answerer_failure_safely(self) -> None:
        def answerer(question: str, snapshot: object) -> str:
            raise RuntimeError("gemini failed with private details")

        reply = build_reply("what is the next gig?", self.snapshot, question_answerer=answerer)

        self.assertIn("I couldn't verify that through the read-only answer engine", reply)
        self.assertIn("/help", reply)
        self.assertNotIn("private details", reply)

    def _store_with_cancellation(self, root: Path) -> BookingWatcherStore:
        store = BookingWatcherStore(root)
        message = ArchivedTelegramMessage(
            chat_id=-1001,
            message_id=42,
            sender_name="Kyle",
            sender_username="kyle",
            text="June 27 is canceled",
            message_date=1719000000,
        )
        signal = BookingSignal("cancellation", "high", 0.75, "June 27", None, "matched cancellation keyword")
        store.add_queue_item(message, signal, calendar_match="unknown", bandsheet_match="unknown")
        return store


if __name__ == "__main__":
    unittest.main()
