import json
import unittest
from urllib.error import HTTPError
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from telegram_bot.telegram_transport import TelegramBot, TelegramConfig, TelegramTransportError


class TelegramTransportTests(unittest.TestCase):
    def test_loads_token_without_exposing_value(self) -> None:
        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:secret-token\n", encoding="utf-8")

            config = TelegramConfig.from_token_file(token_path=token_path)

        self.assertEqual(config.base_url, "https://api.telegram.org/bot123:secret-token")

    def test_loads_token_from_env_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("OTHER=value\nTELEGRAM_BOT_TOKEN=456:env-token\n", encoding="utf-8")

            config = TelegramConfig.from_env_file(env_path=env_path)

        self.assertEqual(config.base_url, "https://api.telegram.org/bot456:env-token")

    def test_process_once_replies_and_persists_offset(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []
        updates = {
            "ok": True,
            "result": [
                {
                    "update_id": 41,
                    "message": {
                        "chat": {"id": 7118814432},
                        "text": "/status",
                    },
                }
            ],
        }

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return updates
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(f"unexpected method {method}")

        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            bot = TelegramBot(
                config=TelegramConfig(token="123:secret-token"),
                state_path=state_path,
                request=request,
                reply_builder=lambda text: f"reply to {text}",
            )

            processed = bot.process_once()

            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(processed, 1)
        self.assertEqual(calls[0], ("getUpdates", {"timeout": 30}))
        self.assertEqual(calls[1][0], "sendMessage")
        self.assertEqual(calls[1][1]["chat_id"], 7118814432)
        self.assertEqual(calls[1][1]["text"], "reply to /status")
        self.assertEqual(state["offset"], 42)

    def test_chatid_command_replies_with_current_chat_id(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 50,
                            "message": {
                                "chat": {"id": -1001234567890},
                                "text": "/chatid",
                            },
                        }
                    ],
                }
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(f"unexpected method {method}")

        with TemporaryDirectory() as temp_dir:
            bot = TelegramBot(
                config=TelegramConfig(token="123:secret-token"),
                state_path=Path(temp_dir) / "state.json",
                request=request,
                reply_builder=lambda text: f"reply to {text}",
            )

            processed = bot.process_once()

        self.assertEqual(processed, 1)
        self.assertEqual(calls[1], ("sendMessage", {"chat_id": -1001234567890, "text": "Chat ID: -1001234567890"}))

    def test_message_handler_can_send_alert_without_command_reply(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []
        reply_calls: list[str] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 51,
                            "message": {
                                "message_id": 77,
                                "date": 1719000000,
                                "from": {"first_name": "Kyle", "username": "kyle"},
                                "chat": {"id": -1001234567890, "type": "group"},
                                "text": "June 27 is canceled",
                            },
                        }
                    ],
                }
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(f"unexpected method {method}")

        def reply_builder(text: str) -> str:
            reply_calls.append(text)
            return f"reply to {text}"

        with TemporaryDirectory() as temp_dir:
            bot = TelegramBot(
                config=TelegramConfig(token="123:secret-token"),
                state_path=Path(temp_dir) / "state.json",
                request=request,
                reply_builder=reply_builder,
                message_handler=lambda message: ["NEON CALENDAR FLAG"],
            )

            processed = bot.process_once()

        self.assertEqual(processed, 1)
        self.assertEqual(reply_calls, [])
        self.assertEqual(calls[1], ("sendMessage", {"chat_id": -1001234567890, "text": "NEON CALENDAR FLAG"}))

    def test_group_question_to_neon_mention_gets_reply(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []
        reply_calls: list[str] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 52,
                            "message": {
                                "chat": {"id": -1001234567890, "type": "group"},
                                "text": "@neon what is the next gig?",
                            },
                        }
                    ],
                }
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(f"unexpected method {method}")

        def reply_builder(text: str) -> str:
            reply_calls.append(text)
            return "next gig reply"

        with TemporaryDirectory() as temp_dir:
            bot = TelegramBot(
                config=TelegramConfig(token="123:secret-token"),
                state_path=Path(temp_dir) / "state.json",
                request=request,
                reply_builder=reply_builder,
            )

            processed = bot.process_once()

        self.assertEqual(processed, 1)
        self.assertEqual(reply_calls, ["what is the next gig?"])
        self.assertEqual(calls[1], ("sendMessage", {"chat_id": -1001234567890, "text": "next gig reply"}))

    def test_get_me_returns_bot_identity(self) -> None:
        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            self.assertEqual(method, "getMe")
            self.assertEqual(payload, {})
            return {"ok": True, "result": {"id": 1, "username": "NeonBotstein_Bot"}}

        bot = TelegramBot(
            config=TelegramConfig(token="123:secret-token"),
            state_path=Path("/tmp/not-used.json"),
            request=request,
            reply_builder=lambda text: text,
        )

        self.assertEqual(bot.get_me()["username"], "NeonBotstein_Bot")

    def test_process_once_uses_existing_offset(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            return {"ok": True, "result": []}

        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text('{"offset": 99}', encoding="utf-8")
            bot = TelegramBot(
                config=TelegramConfig(token="123:secret-token"),
                state_path=state_path,
                request=request,
                reply_builder=lambda text: text,
            )

            processed = bot.process_once()

        self.assertEqual(processed, 0)
        self.assertEqual(calls[0], ("getUpdates", {"timeout": 30, "offset": 99}))

    def test_run_processes_bounded_cycles(self) -> None:
        calls = 0

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {"ok": True, "result": []}

        bot = TelegramBot(
            config=TelegramConfig(token="123:secret-token"),
            state_path=Path("/tmp/not-used.json"),
            request=request,
            reply_builder=lambda text: text,
        )

        processed = bot.run(max_cycles=3, sleep_seconds=0)

        self.assertEqual(processed, 0)
        self.assertEqual(calls, 3)

    def test_cycle_handler_can_send_proactive_reminder(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {"ok": True, "result": []}
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(method)

        bot = TelegramBot(
            config=TelegramConfig(token="123:secret-token"),
            state_path=Path("/tmp/not-used.json"),
            request=request,
            reply_builder=lambda text: text,
            cycle_handler=lambda: [(7118814432, "Draft reminder")],
        )

        bot.process_once()

        self.assertEqual(calls[1], ("sendMessage", {"chat_id": 7118814432, "text": "Draft reminder"}))

    def test_http_errors_are_wrapped_without_token_details(self) -> None:
        bot = TelegramBot(
            config=TelegramConfig(token="123:secret-token"),
            state_path=Path("/tmp/not-used.json"),
            reply_builder=lambda text: text,
        )
        error = HTTPError(
            url="https://api.telegram.org/bot123:secret-token/getUpdates",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None,
        )

        with patch("telegram_bot.telegram_transport.urlopen", side_effect=error):
            with self.assertRaises(TelegramTransportError) as context:
                bot.process_once()

        self.assertIn("401", str(context.exception))
        self.assertNotIn("secret-token", str(context.exception))


if __name__ == "__main__":
    unittest.main()
