import unittest
from pathlib import Path


class LaunchAssetsTests(unittest.TestCase):
    def test_launchd_plist_uses_repo_wrapper(self) -> None:
        root = Path(__file__).resolve().parents[1]
        plist_path = root / "launchd" / "com.neonblonde.gigcopilot.plist"

        text = plist_path.read_text(encoding="utf-8")

        self.assertIn("<string>com.neonblonde.gigcopilot</string>", text)
        self.assertIn(f"<string>{root / 'scripts' / 'run_gig_copilot.sh'}</string>", text)
        self.assertIn("<key>KeepAlive</key>", text)
        self.assertIn("<true/>", text)

    def test_wrapper_runs_bot_loop_from_lane_root(self) -> None:
        root = Path(__file__).resolve().parents[1]
        wrapper = root / "scripts" / "run_gig_copilot.sh"

        text = wrapper.read_text(encoding="utf-8")

        self.assertIn("cd \"$LANE_ROOT\"", text)
        self.assertIn('export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"', text)
        self.assertIn('PYTHON_BIN="${GIG_COPILOT_PYTHON:-/opt/homebrew/bin/python3}"', text)
        self.assertIn('"$PYTHON_BIN" -m gig_copilot_bot run', text)
        self.assertIn("--token-file \"$TOKEN_FILE\"", text)
        self.assertIn("--state-file \"$STATE_FILE\"", text)
        self.assertIn("--profiles-file \"$PROFILES_FILE\"", text)
        self.assertIn('GROUP_CHAT_ID="${GIG_COPILOT_GROUP_CHAT_ID:--1004424634571}"', text)
        self.assertIn("--enable-gig-day-updates", text)
        self.assertIn("--group-chat-id \"$GROUP_CHAT_ID\"", text)
        self.assertIn("--receipt-file \"$RECEIPT_FILE\"", text)


if __name__ == "__main__":
    unittest.main()
