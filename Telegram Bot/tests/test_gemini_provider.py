import unittest
from unittest.mock import patch

from telegram_bot.providers.gemini import resolve_gemini_command


class GeminiProviderTests(unittest.TestCase):
    def test_resolves_homebrew_gemini_when_launchd_path_cannot_find_it(self) -> None:
        with patch("telegram_bot.providers.gemini.shutil.which", return_value=None):
            command = resolve_gemini_command()

        self.assertEqual(command, ("/opt/homebrew/bin/gemini",))

    def test_prefers_path_gemini_when_available(self) -> None:
        with patch("telegram_bot.providers.gemini.shutil.which", return_value="/custom/bin/gemini"):
            command = resolve_gemini_command()

        self.assertEqual(command, ("/custom/bin/gemini",))


if __name__ == "__main__":
    unittest.main()
