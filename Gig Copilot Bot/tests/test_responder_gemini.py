import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gig_copilot_bot.profile_store import ProfileStore
from gig_copilot_bot.responder import build_reply


class FakeGemini:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "Gemini-powered Mike-only logistics answer."


class ResponderGeminiTests(unittest.TestCase):
    def test_unknown_message_can_use_gemini_when_available(self) -> None:
        gemini = FakeGemini()

        with TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            build_reply("/onboard", store)

            reply = build_reply("What should I do before the show?", store, gemini=gemini)

        self.assertEqual(reply, "Gemini-powered Mike-only logistics answer.")
        self.assertIn("Mike-only", gemini.prompts[0])
        self.assertIn("What should I do before the show?", gemini.prompts[0])

    def test_fixed_commands_do_not_call_gemini(self) -> None:
        gemini = FakeGemini()

        with TemporaryDirectory() as temp_dir:
            reply = build_reply("/help", ProfileStore(Path(temp_dir) / "profiles.json"), gemini=gemini)

        self.assertIn("/onboard", reply)
        self.assertEqual(gemini.prompts, [])


if __name__ == "__main__":
    unittest.main()
