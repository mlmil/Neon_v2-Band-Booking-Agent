import os
import unittest
from urllib.error import HTTPError
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from gig_copilot_bot.gemini_provider import GeminiProvider, GeminiProviderError, load_gemini_api_key


class GeminiProviderTests(unittest.TestCase):
    def test_loads_api_key_from_environment(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}, clear=True):
            self.assertEqual(load_gemini_api_key(), "env-key")

    def test_loads_api_key_from_file_when_env_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            key_path = Path(temp_dir) / "gemini_api_key.txt"
            key_path.write_text("file-key\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(load_gemini_api_key(key_path=key_path), "file-key")

    def test_generates_text_from_injected_requester(self) -> None:
        requests: list[dict[str, object]] = []

        def requester(url: str, payload: dict[str, object], timeout: int) -> dict[str, object]:
            requests.append({"url": url, "payload": payload, "timeout": timeout})
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "Drafted day-of-show response."},
                            ]
                        }
                    }
                ]
            }

        provider = GeminiProvider(api_key="test-key", requester=requester)

        response = provider.generate("Write a logistics reply.")

        self.assertEqual(response, "Drafted day-of-show response.")
        self.assertIn("gemini-2.5-flash", requests[0]["url"])
        self.assertIn("contents", requests[0]["payload"])
        self.assertEqual(requests[0]["payload"]["generationConfig"]["thinkingConfig"]["thinkingBudget"], 0)

    def test_wraps_http_errors_without_key_details(self) -> None:
        error = HTTPError(
            url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=secret",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        def requester(url: str, payload: dict[str, object], timeout: int) -> dict[str, object]:
            raise error

        provider = GeminiProvider(api_key="secret", requester=requester)

        with self.assertRaises(GeminiProviderError) as context:
            provider.generate("hello")

        self.assertIn("HTTP 404", str(context.exception))
        self.assertNotIn("secret", str(context.exception))


if __name__ == "__main__":
    unittest.main()
