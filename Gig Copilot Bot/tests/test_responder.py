import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gig_copilot_bot.models import MemberProfile
from gig_copilot_bot.profile_store import ProfileStore
from gig_copilot_bot.responder import build_reply


class ResponderTests(unittest.TestCase):
    def test_start_introduces_mike_only_test_mode(self) -> None:
        with TemporaryDirectory() as temp_dir:
            reply = build_reply("/start", ProfileStore(Path(temp_dir) / "profiles.json"))

        self.assertIn("GigCopilotNeon_Bot", reply)
        self.assertIn("Mike-only test mode", reply)

    def test_help_lists_commands(self) -> None:
        with TemporaryDirectory() as temp_dir:
            reply = build_reply("/help", ProfileStore(Path(temp_dir) / "profiles.json"))

        self.assertIn("/onboard", reply)
        self.assertIn("/simulate-show-day", reply)

    def test_onboard_saves_mike_default_profile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")

            reply = build_reply("/onboard", store)

            profile = store.load_profile("mike")

        self.assertIn("Mike onboarding saved", reply)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.default_origin_city, "Ventura")
        self.assertEqual(profile.pa_load_in_arrival_minutes, 120)

    def test_profile_shows_saved_profile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile(
                MemberProfile(
                    member_id="mike",
                    name="Mike",
                    role="Bass + PA setup",
                    default_origin_city="Ventura",
                    alternate_origin_cities=["Oxnard"],
                    standard_arrival_minutes=60,
                    pa_load_in_arrival_minutes=120,
                    live_location_required=True,
                )
            )

            reply = build_reply("/profile", store)

        self.assertIn("Mike", reply)
        self.assertIn("Ventura", reply)
        self.assertIn("PA/load-in arrival: 120 minutes", reply)

    def test_profile_prompts_for_onboarding_when_missing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            reply = build_reply("/profile", ProfileStore(Path(temp_dir) / "profiles.json"))

        self.assertIn("No Mike profile saved yet", reply)

    def test_simulate_show_day_is_mike_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            reply = build_reply("/simulate-show-day", ProfileStore(Path(temp_dir) / "profiles.json"))

        self.assertIn("SIMULATION - Mike only", reply)
        self.assertIn("Band-wide kickoff preview", reply)
        self.assertIn("Mike personal route prompt", reply)
        self.assertIn("No band messages sent", reply)

    def test_status_reports_profile_storage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            build_reply("/onboard", store)

            reply = build_reply("/status", store)

        self.assertIn("mode: Mike-only test", reply)
        self.assertIn("Mike profile: saved", reply)


if __name__ == "__main__":
    unittest.main()
