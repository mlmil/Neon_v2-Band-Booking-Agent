import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TelegramRequest = Callable[[str, dict[str, object]], dict[str, object]]
ReplyBuilder = Callable[[str], str]


class TelegramTransportError(RuntimeError):
    """Raised when Telegram API transport fails without exposing credentials."""


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    api_root: str = "https://api.telegram.org"

    @classmethod
    def from_token_file(cls, token_path: Path) -> "TelegramConfig":
        token = token_path.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("Telegram token file is empty")
        return cls(token=token)

    @property
    def base_url(self) -> str:
        return f"{self.api_root}/bot{self.token}"


class TelegramBot:
    def __init__(
        self,
        *,
        config: TelegramConfig,
        state_path: Path,
        request: TelegramRequest | None = None,
        reply_builder: ReplyBuilder,
    ) -> None:
        self._config = config
        self._state_path = state_path
        self._request = request or self._telegram_request
        self._reply_builder = reply_builder

    def process_once(self) -> int:
        updates = self._get_updates()
        processed = 0
        max_update_id: int | None = None
        for update in updates:
            if not isinstance(update, dict):
                continue
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                max_update_id = update_id if max_update_id is None else max(max_update_id, update_id)
            message = update.get("message")
            if not isinstance(message, dict):
                continue
            text = message.get("text")
            chat = message.get("chat")
            if not isinstance(text, str) or not isinstance(chat, dict):
                continue
            chat_id = chat.get("id")
            if not isinstance(chat_id, int):
                continue
            reply = f"Chat ID: {chat_id}" if text.strip().lower() == "/chatid" else self._reply_builder(text)
            self._send_message(chat_id, reply)
            processed += 1
        if max_update_id is not None:
            self._write_offset(max_update_id + 1)
        return processed

    def get_me(self) -> dict[str, object]:
        response = self._request("getMe", {})
        if response.get("ok") is not True:
            raise RuntimeError("Telegram getMe failed")
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("Telegram getMe returned invalid result")
        return result

    def send_message(self, chat_id: int, text: str) -> None:
        self._send_message(chat_id, text)

    def run(self, *, max_cycles: int | None = None, sleep_seconds: float = 5) -> int:
        processed_total = 0
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            processed_total += self.process_once()
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                time.sleep(sleep_seconds)
        return processed_total

    def _get_updates(self) -> list[object]:
        payload: dict[str, object] = {"timeout": 30}
        offset = self._read_offset()
        if offset is not None:
            payload["offset"] = offset
        response = self._request("getUpdates", payload)
        if response.get("ok") is not True:
            raise RuntimeError("Telegram getUpdates failed")
        result = response.get("result")
        if not isinstance(result, list):
            raise RuntimeError("Telegram getUpdates returned invalid result")
        return result

    def _send_message(self, chat_id: int, text: str) -> None:
        response = self._request("sendMessage", {"chat_id": chat_id, "text": text})
        if response.get("ok") is not True:
            raise RuntimeError("Telegram sendMessage failed")

    def _telegram_request(self, method: str, payload: dict[str, object]) -> dict[str, object]:
        encoded = urlencode(payload).encode("utf-8")
        request = Request(f"{self._config.base_url}/{method}", data=encoded, method="POST")
        try:
            with urlopen(request, timeout=35) as response:
                decoded = json.load(response)
        except HTTPError as exc:
            raise TelegramTransportError(f"Telegram API returned HTTP {exc.code} for {method}") from exc
        except (OSError, URLError, TimeoutError) as exc:
            raise TelegramTransportError(f"Telegram API request failed for {method}") from exc
        if not isinstance(decoded, dict):
            raise RuntimeError("Telegram returned invalid JSON")
        return decoded

    def _read_offset(self) -> int | None:
        if not self._state_path.exists():
            return None
        try:
            payload = json.loads(self._state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        offset = payload.get("offset") if isinstance(payload, dict) else None
        return offset if isinstance(offset, int) else None

    def _write_offset(self, offset: int) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps({"offset": offset}, indent=2), encoding="utf-8")
