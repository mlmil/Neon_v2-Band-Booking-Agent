import contextlib
import io
import json
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from pathlib import Path

from telegram_bot.cli import main
from telegram_bot.telegram_transport import TelegramTransportError


class CliTests(unittest.TestCase):
    def test_prints_bandsheet_snapshot_from_fixture(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["bandsheet-snapshot", "--fixture", str(fixture)])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["snapshot"]["booked_gigs"][0]["venue_name"], "Santa Barbara Yacht Club")

    def test_prints_reply_from_fixture_snapshot(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["reply", "/gigs", "--fixture", str(fixture)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Upcoming gigs:", output.getvalue())
        self.assertIn("Santa Barbara Yacht Club", output.getvalue())

    def test_prints_free_form_reply_through_gemini_answerer(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        output = io.StringIO()

        with patch("telegram_bot.cli.GeminiQuestionAnswerer") as answerer_class:
            answerer_class.return_value.return_value = "Next gig answer."
            with contextlib.redirect_stdout(output):
                exit_code = main(["reply", "what is the next gig?", "--fixture", str(fixture)])

        self.assertEqual(exit_code, 0)
        answerer_class.assert_called_once()
        self.assertEqual(output.getvalue().strip(), "Next gig answer.")

    def test_prints_rehearsals_reply_from_provider(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        output = io.StringIO()

        with patch("telegram_bot.cli.FreshgroundRehearsalProvider") as provider_class:
            provider_class.return_value.upcoming.return_value = ["Thu 7-16 @ 7:00pm - - 10 Neon Blond"]
            with contextlib.redirect_stdout(output):
                exit_code = main(["reply", "/rehearsals", "--fixture", str(fixture)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Freshground rehearsals:", output.getvalue())
        self.assertIn("Neon Blond", output.getvalue())

    def test_prints_closeout_reply_from_provider(self) -> None:
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "bandsheet-data.sample.json"
        output = io.StringIO()

        with patch("telegram_bot.cli.CloseoutQueueProvider") as provider_class:
            provider_class.return_value.needs_closeout.return_value = ["2026-06-06 - Tony's Pizza (Ventura): Ask Mike for pay."]
            with contextlib.redirect_stdout(output):
                exit_code = main(["reply", "/closeout", "--fixture", str(fixture)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Post-gig closeout queue:", output.getvalue())
        self.assertIn("Tony's Pizza", output.getvalue())

    def test_poll_once_uses_transport_with_default_paths(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.TelegramBot") as bot_class:
            bot_class.return_value.process_once.return_value = 2
            with contextlib.redirect_stdout(output):
                exit_code = main(["poll-once"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), "processed 2 update(s)")
        bot_class.return_value.process_once.assert_called_once_with()

    def test_poll_once_wires_booking_watcher_service(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.BookingWatcherService") as service_class:
            with patch("telegram_bot.cli.GeminiQuestionAnswerer") as answerer_class:
                answerer_class.return_value = object()
                with patch("telegram_bot.cli.TelegramBot") as bot_class:
                    bot_class.return_value.process_once.return_value = 0
                    with contextlib.redirect_stdout(output):
                        exit_code = main(["poll-once", "--fixture", "fixtures/bandsheet-data.sample.json"])

        self.assertEqual(exit_code, 0)
        service_class.assert_called_once()
        answerer_class.assert_called_once()
        _, kwargs = bot_class.call_args
        self.assertEqual(kwargs["message_handler"], service_class.return_value.handle_incoming_message)

    def test_poll_once_can_disable_gemini_fallback(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.BookingWatcherService") as service_class:
            with patch("telegram_bot.cli.GeminiQuestionAnswerer") as answerer_class:
                with patch("telegram_bot.cli.TelegramBot") as bot_class:
                    bot_class.return_value.process_once.return_value = 0
                    with contextlib.redirect_stdout(output):
                        exit_code = main(["poll-once", "--fixture", "fixtures/bandsheet-data.sample.json", "--no-gemini"])

        self.assertEqual(exit_code, 0)
        service_class.assert_called_once()
        answerer_class.assert_not_called()
        _, kwargs = bot_class.call_args
        self.assertEqual(kwargs["message_handler"], service_class.return_value.handle_incoming_message)

    def test_poll_once_reports_transport_error_without_traceback(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.TelegramBot") as bot_class:
            bot_class.return_value.process_once.side_effect = TelegramTransportError("Telegram API returned HTTP 401")
            with contextlib.redirect_stdout(output):
                exit_code = main(["poll-once"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(output.getvalue().strip(), "Telegram unavailable: Telegram API returned HTTP 401")

    def test_poll_once_can_use_env_file_token(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.TelegramConfig") as config_class:
            with patch("telegram_bot.cli.TelegramBot") as bot_class:
                config_class.from_env_file.return_value = object()
                bot_class.return_value.process_once.return_value = 0
                with contextlib.redirect_stdout(output):
                    exit_code = main(["poll-once", "--env-file", "/tmp/hermes.env"])

        self.assertEqual(exit_code, 0)
        config_class.from_env_file.assert_called_once_with(Path("/tmp/hermes.env"))
        config_class.from_token_file.assert_not_called()

    def test_run_uses_transport_loop_with_max_cycles(self) -> None:
        output = io.StringIO()

        with patch("telegram_bot.cli.TelegramBot") as bot_class:
            bot_class.return_value.run.return_value = 4
            with contextlib.redirect_stdout(output):
                exit_code = main(["run", "--max-cycles", "2", "--sleep-seconds", "0"])

        self.assertEqual(exit_code, 0)
        bot_class.return_value.run.assert_called_once_with(max_cycles=2, sleep_seconds=0.0)
        self.assertEqual(output.getvalue().strip(), "processed 4 update(s)")

    def test_health_reports_wrong_bot_identity(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / "hermes.env"
            env_file.write_text("TELEGRAM_BOT_TOKEN=123:test-token\n", encoding="utf-8")
            with patch("telegram_bot.cli.TelegramBot") as bot_class:
                bot_class.return_value.get_me.return_value = {"username": "Diane_mikes_ass_bot"}
                with contextlib.redirect_stdout(output):
                    exit_code = main(["health", "--env-file", str(env_file)])

        self.assertEqual(exit_code, 1)
        self.assertIn("wrong bot: Diane_mikes_ass_bot", output.getvalue())


if __name__ == "__main__":
    unittest.main()
