import json
import os
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GeminiRequester = Callable[[str, dict[str, object], int], dict[str, object]]
DEFAULT_GEMINI_KEY_PATH = Path.home() / ".hermes" / "secure" / "gemini_api_key.txt"


class GeminiProviderError(RuntimeError):
    """Raised when Gemini generation fails without exposing credentials."""


def load_gemini_api_key(key_path: Path = DEFAULT_GEMINI_KEY_PATH) -> str | None:
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key.strip()
    if key_path.exists():
        key = key_path.read_text(encoding="utf-8").strip()
        return key or None
    return None


class GeminiProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        requester: GeminiRequester | None = None,
        timeout: int = 30,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._requester = requester or self._request
        self._timeout = timeout

    def generate(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?"
            + urlencode({"key": self._api_key})
        )
        payload: dict[str, object] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 500,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        try:
            response = self._requester(url, payload, self._timeout)
        except HTTPError as exc:
            raise GeminiProviderError(f"Gemini API returned HTTP {exc.code}") from exc
        except (OSError, URLError, TimeoutError) as exc:
            raise GeminiProviderError("Gemini API request failed") from exc
        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: dict[str, object]) -> str:
        candidates = response.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("Gemini returned no candidates")
        first = candidates[0]
        if not isinstance(first, dict):
            raise RuntimeError("Gemini candidate is invalid")
        content = first.get("content")
        if not isinstance(content, dict):
            raise RuntimeError("Gemini content is invalid")
        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            raise RuntimeError("Gemini content has no parts")
        first_part = parts[0]
        if not isinstance(first_part, dict) or not isinstance(first_part.get("text"), str):
            raise RuntimeError("Gemini text is missing")
        return first_part["text"].strip()

    @staticmethod
    def _request(url: str, payload: dict[str, object], timeout: int) -> dict[str, object]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            decoded = json.load(response)
        if not isinstance(decoded, dict):
            raise RuntimeError("Gemini returned invalid JSON")
        return decoded
