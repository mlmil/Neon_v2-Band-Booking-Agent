import unittest
from pathlib import Path


class LaunchAssetsTests(unittest.TestCase):
    def test_launchd_plist_uses_repo_wrapper(self) -> None:
        root = Path(__file__).resolve().parents[1]
        plist_path = root / "launchd" / "com.neonblonde.neonbotstein.plist"

        text = plist_path.read_text(encoding="utf-8")

        self.assertIn("<string>com.neonblonde.neonbotstein</string>", text)
        self.assertIn(f"<string>{root / 'scripts' / 'run_neonbotstein.sh'}</string>", text)
        self.assertIn("<key>KeepAlive</key>", text)
        self.assertIn("<true/>", text)

    def test_wrapper_runs_bot_loop_from_lane_root(self) -> None:
        root = Path(__file__).resolve().parents[1]
        wrapper = root / "scripts" / "run_neonbotstein.sh"

        text = wrapper.read_text(encoding="utf-8")

        self.assertIn("cd \"$LANE_ROOT\"", text)
        self.assertIn('NEON_BLONDE_ROOT="${NEON_BLONDE_ROOT:-/Volumes/VADER/Manifold/Neon_Blonde}"', text)
        self.assertIn('export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"', text)
        self.assertIn("export NEON_BLONDE_ROOT", text)
        self.assertIn('PYTHON_BIN="${NEONBOTSTEIN_PYTHON:-/opt/homebrew/bin/python3}"', text)
        self.assertIn('"$PYTHON_BIN" -m telegram_bot run', text)
        self.assertIn("--token-file \"$TOKEN_FILE\"", text)


if __name__ == "__main__":
    unittest.main()
