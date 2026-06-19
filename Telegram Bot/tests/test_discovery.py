import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from telegram_bot.discovery import DiscoveryError, discover_repo_context


class DiscoveryTests(unittest.TestCase):
    def test_discovers_repo_context_from_lane_root(self) -> None:
        lane_root = Path(__file__).resolve().parents[1]

        context = discover_repo_context(lane_root=lane_root)

        self.assertEqual(context.lane_name, "Telegram Bot")
        self.assertEqual(context.lane_root, lane_root)
        self.assertTrue((context.repo_root / "SKILL.md").exists())
        self.assertTrue((context.repo_root / "README.md").exists())

    def test_rejects_wrong_lane_name(self) -> None:
        wrong_lane = Path("/tmp/not-telegram-bot")

        with self.assertRaises(DiscoveryError):
            discover_repo_context(lane_root=wrong_lane)

    def test_rejects_missing_repo_markers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            lane_root = Path(temp_dir) / "Telegram Bot"
            lane_root.mkdir()

            with self.assertRaises(DiscoveryError) as context:
                discover_repo_context(lane_root=lane_root)

        self.assertIn("Repo root is missing required markers", str(context.exception))


if __name__ == "__main__":
    unittest.main()
