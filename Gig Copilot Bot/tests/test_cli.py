import contextlib
import io
import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from gig_copilot_bot.cli import main
from gig_copilot_bot.gemini_provider import GeminiProviderError
from gig_copilot_bot.telegram_transport import TelegramTransportError


class CliTests(unittest.TestCase):
    def test_reply_uses_profile_store(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(["reply", "/status", "--profiles-file", str(Path(temp_dir) / "profiles.json")])

        self.assertEqual(exit_code, 0)
        self.assertIn("mode: Mike-only test", output.getvalue())

    def test_reply_can_use_gemini_for_freeform_message(self) -> None:
        output = io.StringIO()

        with patch("gig_copilot_bot.cli.load_gemini_api_key", return_value="test-key"):
            with patch("gig_copilot_bot.cli.GeminiProvider") as provider_class:
                provider_class.return_value.generate.return_value = "Gemini says prep your show bag."
                with TemporaryDirectory() as temp_dir:
                    with contextlib.redirect_stdout(output):
                        exit_code = main(
                            [
                                "reply",
                                "What should I do today?",
                                "--profiles-file",
                                str(Path(temp_dir) / "profiles.json"),
                            ]
                        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), "Gemini says prep your show bag.")

    def test_reply_falls_back_when_gemini_fails(self) -> None:
        output = io.StringIO()

        with patch("gig_copilot_bot.cli.load_gemini_api_key", return_value="test-key"):
            with patch("gig_copilot_bot.cli.GeminiProvider") as provider_class:
                provider_class.return_value.generate.side_effect = GeminiProviderError("Gemini API returned HTTP 404")
                with TemporaryDirectory() as temp_dir:
                    with contextlib.redirect_stdout(output):
                        exit_code = main(
                            [
                                "reply",
                                "What should I do today?",
                                "--profiles-file",
                                str(Path(temp_dir) / "profiles.json"),
                            ]
                        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Gemini unavailable", output.getvalue())

    def test_health_reports_expected_bot_identity(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:test-token\n", encoding="utf-8")
            with patch("gig_copilot_bot.cli.TelegramBot") as bot_class:
                bot_class.return_value.get_me.return_value = {"username": "GigCopilotNeon_Bot"}
                with contextlib.redirect_stdout(output):
                    exit_code = main(["health", "--token-file", str(token_path)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), "ok: GigCopilotNeon_Bot")

    def test_poll_once_reports_transport_error_without_traceback(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:test-token\n", encoding="utf-8")
            with patch("gig_copilot_bot.cli.TelegramBot") as bot_class:
                bot_class.return_value.process_once.side_effect = TelegramTransportError("Telegram API returned HTTP 401")
                with contextlib.redirect_stdout(output):
                    exit_code = main(["poll-once", "--token-file", str(token_path)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(output.getvalue().strip(), "Telegram unavailable: Telegram API returned HTTP 401")

    def test_run_uses_transport_loop_with_max_cycles(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:test-token\n", encoding="utf-8")
            with patch("gig_copilot_bot.cli.TelegramBot") as bot_class:
                bot_class.return_value.run.return_value = 3
                with contextlib.redirect_stdout(output):
                    exit_code = main(
                        [
                            "run",
                            "--token-file",
                            str(token_path),
                            "--state-file",
                            str(Path(temp_dir) / "state.json"),
                            "--profiles-file",
                            str(Path(temp_dir) / "profiles.json"),
                            "--max-cycles",
                            "2",
                            "--sleep-seconds",
                            "0",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        bot_class.return_value.run.assert_called_once_with(max_cycles=2, sleep_seconds=0.0)
        self.assertEqual(output.getvalue().strip(), "processed 3 update(s)")

    def test_gig_day_update_dry_run_reports_without_sending(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            with patch(
                "gig_copilot_bot.cli._load_live_calendar_gigs",
                return_value=[{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}],
            ):
                with patch("gig_copilot_bot.cli.TelegramBot") as bot_class:
                    with contextlib.redirect_stdout(output):
                        exit_code = main(
                            [
                                "gig-day-update",
                                "--date",
                                "2026-07-18",
                                "--dry-run",
                                "--receipt-file",
                                str(Path(temp_dir) / "receipts.json"),
                            ]
                        )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["would_send"], 1)
        bot_class.return_value.send_message.assert_not_called()

    def test_gig_day_update_sends_to_configured_group(self) -> None:
        output = io.StringIO()

        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:test-token\n", encoding="utf-8")
            with patch(
                "gig_copilot_bot.cli._load_live_calendar_gigs",
                return_value=[{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}],
            ):
                with patch("gig_copilot_bot.cli.TelegramBot") as bot_class:
                    with contextlib.redirect_stdout(output):
                        exit_code = main(
                            [
                                "gig-day-update",
                                "--date",
                                "2026-07-18",
                                "--token-file",
                                str(token_path),
                                "--group-chat-id",
                                "-1004424634571",
                                "--receipt-file",
                                str(Path(temp_dir) / "receipts.json"),
                            ]
                        )

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["sent"], 1)
        bot_class.return_value.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
