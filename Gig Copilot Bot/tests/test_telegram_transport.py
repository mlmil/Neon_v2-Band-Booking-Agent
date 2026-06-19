import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gig_copilot_bot.telegram_transport import TelegramBot, TelegramConfig


class TelegramTransportTests(unittest.TestCase):
    def test_loads_token_from_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            token_path = Path(temp_dir) / "token.txt"
            token_path.write_text("123:test-token\n", encoding="utf-8")

            config = TelegramConfig.from_token_file(token_path)

        self.assertEqual(config.base_url, "https://api.telegram.org/bot123:test-token")

    def test_process_once_sends_reply_and_writes_offset(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 10,
                            "message": {
                                "chat": {"id": 7118814432},
                                "text": "/status",
                            },
                        }
                    ],
                }
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(method)

        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            bot = TelegramBot(
                config=TelegramConfig(token="123:test-token"),
                state_path=state_path,
                request=request,
                reply_builder=lambda text: f"reply: {text}",
            )

            processed = bot.process_once()

            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(processed, 1)
        self.assertEqual(calls[1], ("sendMessage", {"chat_id": 7118814432, "text": "reply: /status"}))
        self.assertEqual(state["offset"], 11)

    def test_chatid_command_replies_with_current_chat_id(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append((method, payload))
            if method == "getUpdates":
                return {
                    "ok": True,
                    "result": [
                        {
                            "update_id": 11,
                            "message": {
                                "chat": {"id": 123456789},
                                "text": "/chatid",
                            },
                        }
                    ],
                }
            if method == "sendMessage":
                return {"ok": True, "result": {"message_id": 1}}
            raise AssertionError(method)

        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            bot = TelegramBot(
                config=TelegramConfig(token="123:test-token"),
                state_path=state_path,
                request=request,
                reply_builder=lambda text: f"reply: {text}",
            )

            processed = bot.process_once()

        self.assertEqual(processed, 1)
        self.assertEqual(calls[1], ("sendMessage", {"chat_id": 123456789, "text": "Chat ID: 123456789"}))

    def test_get_me_returns_identity(self) -> None:
        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            self.assertEqual(method, "getMe")
            return {"ok": True, "result": {"username": "GigCopilotNeon_Bot"}}

        bot = TelegramBot(
            config=TelegramConfig(token="123:test-token"),
            state_path=Path("/tmp/not-used.json"),
            request=request,
            reply_builder=lambda text: text,
        )

        self.assertEqual(bot.get_me()["username"], "GigCopilotNeon_Bot")

    def test_run_processes_bounded_cycles(self) -> None:
        calls = 0

        def request(method: str, payload: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {"ok": True, "result": []}

        bot = TelegramBot(
            config=TelegramConfig(token="123:test-token"),
            state_path=Path("/tmp/not-used.json"),
            request=request,
            reply_builder=lambda text: text,
        )

        processed = bot.run(max_cycles=3, sleep_seconds=0)

        self.assertEqual(processed, 0)
        self.assertEqual(calls, 3)


if __name__ == "__main__":
    unittest.main()
