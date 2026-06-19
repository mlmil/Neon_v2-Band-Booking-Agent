import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from telegram_bot.providers.pending_drafts import PendingDraftsProvider


class PendingDraftsProviderTests(unittest.TestCase):
    def test_loads_pending_reply_drafts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pending.json"
            path.write_text(
                json.dumps(
                    {
                        "replies": [
                            {
                                "to": ["rockstarentertainment805@gmail.com"],
                                "from_name": "Phillip Thomas",
                                "subject": "Re: New confirmed date",
                                "body": "Hi Phillip,\n\nThanks for the update.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            drafts = PendingDraftsProvider(path).list_drafts()

        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0].from_name, "Phillip Thomas")
        self.assertEqual(drafts[0].subject, "Re: New confirmed date")
        self.assertIn("Thanks for the update", drafts[0].body)

    def test_missing_or_invalid_file_returns_empty_list(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(PendingDraftsProvider(root / "missing.json").list_drafts(), [])
            invalid = root / "invalid.json"
            invalid.write_text("not json", encoding="utf-8")
            self.assertEqual(PendingDraftsProvider(invalid).list_drafts(), [])


if __name__ == "__main__":
    unittest.main()
