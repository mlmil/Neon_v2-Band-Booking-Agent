import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gig_copilot_bot.models import MemberProfile
from gig_copilot_bot.profile_store import ProfileStore


class ProfileStoreTests(unittest.TestCase):
    def test_missing_profile_returns_none(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")

            self.assertIsNone(store.load_profile("mike"))

    def test_saves_and_loads_member_profile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "profiles.json"
            store = ProfileStore(path)
            profile = MemberProfile(
                member_id="mike",
                name="Mike",
                role="Bass + PA setup",
                default_origin_city="Ventura",
                alternate_origin_cities=["Oxnard", "Santa Barbara"],
                standard_arrival_minutes=60,
                pa_load_in_arrival_minutes=120,
                live_location_required=True,
            )

            store.save_profile(profile)

            loaded = store.load_profile("mike")
            self.assertEqual(loaded, profile)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["profiles"]["mike"]["default_origin_city"], "Ventura")


if __name__ == "__main__":
    unittest.main()
