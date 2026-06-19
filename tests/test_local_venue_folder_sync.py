import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from scripts.local_venue_folder_sync import (
    DEFAULT_LOCAL_MODEL_URL,
    LocalGig,
    build_local_model_prompt,
    clean_calendar_venue_title,
    filter_gigs_on_or_after,
    gig_folder_name,
    request_local_model_digest,
    sync_local_gig_folder,
)


class LocalVenueFolderSyncTests(unittest.TestCase):
    def test_gig_folder_name_uses_venue_and_date(self):
        self.assertEqual(gig_folder_name("Tony's Pizza", "2026-08-15"), "Tonys Pizza - 2026-08-15")

    def test_sync_uses_existing_venue_folder_and_creates_gig_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tonys Pizza").mkdir()
            gig = LocalGig(venue="Tony's Pizza", city="Ventura", date="2026-08-15", time="7pm")

            result = sync_local_gig_folder(gig, root)

            self.assertEqual(result["status"], "success")
            self.assertFalse(result["created_venue_folder"])
            self.assertTrue(Path(result["gig_folder"]).exists())
            self.assertEqual(Path(result["gig_folder"]).name, "Tonys Pizza - 2026-08-15")
            self.assertTrue((Path(result["gig_folder"]) / "LOCAL_GIG_RECEIPT.md").exists())

    def test_sync_creates_new_venue_folder_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gig = LocalGig(venue="Ms Special", city="Goleta", date="2026-08-15", time="7pm")

            result = sync_local_gig_folder(gig, root)

            self.assertEqual(result["status"], "needs_review")
            self.assertTrue(result["created_venue_folder"])
            self.assertTrue((root / "Ms Special").exists())
            self.assertTrue(Path(result["gig_folder"]).exists())

    def test_sync_routes_test_venue_under_test_venues_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gig = LocalGig(venue="Club Bobaloo", city="Ventura", date="2026-10-07", time="7pm")

            result = sync_local_gig_folder(gig, root)

            self.assertEqual(result["status"], "success")
            self.assertEqual(Path(result["venue_folder"]), root / "_Test Venues" / "Club Babaloo")
            self.assertTrue(Path(result["gig_folder"]).exists())

    def test_sync_is_idempotent_for_existing_gig_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gig = LocalGig(venue="Leashless", city="Ventura", date="2026-07-18", time="6pm")

            first = sync_local_gig_folder(gig, root)
            second = sync_local_gig_folder(gig, root)

            self.assertTrue(first["created_gig_folder"])
            self.assertFalse(second["created_gig_folder"])
            self.assertEqual(first["gig_folder"], second["gig_folder"])

    def test_local_model_prompt_summarizes_safe_task(self):
        gig = LocalGig(venue="Leashless", city="Ventura", date="2026-07-18", time="6pm")

        prompt = build_local_model_prompt(gig)

        self.assertIn("Leashless", prompt)
        self.assertIn("read-only", prompt)
        self.assertIn("Do not", prompt)

    def test_local_model_defaults_to_lm_studio_chat_completions(self):
        self.assertEqual(DEFAULT_LOCAL_MODEL_URL, "http://127.0.0.1:1234/v1/chat/completions")

    def test_local_model_uses_openai_chat_contract(self):
        gig = LocalGig(venue="Leashless", city="Ventura", date="2026-07-18", time="6pm")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return BytesIO(
                    b'{"choices":[{"message":{"content":"Digest ready"}}]}'
                ).read()

        with patch("urllib.request.urlopen", return_value=Response()) as urlopen:
            digest = request_local_model_digest(gig, model="test-model")

        request = urlopen.call_args.args[0]
        payload = __import__("json").loads(request.data.decode("utf-8"))
        self.assertEqual(digest, "Digest ready")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn("Leashless", payload["messages"][0]["content"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 120)

    def test_sync_does_not_overwrite_existing_local_model_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gig = LocalGig(venue="Leashless", city="Ventura", date="2026-07-18", time="6pm")
            first = sync_local_gig_folder(gig, root)
            model_path = Path(first["local_model_path"])
            model_path.write_text("manual notes\n", encoding="utf-8")

            sync_local_gig_folder(gig, root)

            self.assertEqual(model_path.read_text(encoding="utf-8"), "manual notes\n")

    def test_filter_gigs_on_or_after_keeps_only_current_and_future(self):
        gigs = [
            LocalGig("The Sewer", "Ventura", "2026-01-17", "8pm"),
            LocalGig("Leashless", "Ventura", "2026-07-18", "6pm"),
        ]

        filtered = filter_gigs_on_or_after(gigs, "2026-06-09")

        self.assertEqual(filtered, [LocalGig("Leashless", "Ventura", "2026-07-18", "6pm")])

    def test_clean_calendar_venue_title_removes_legacy_prefix_and_aliases(self):
        self.assertEqual(clean_calendar_venue_title("Gig at Fig Mountain Brewing"), "Fig Mountain")
        self.assertEqual(clean_calendar_venue_title("Fox Wine Company"), "Fox Wine")
        self.assertEqual(clean_calendar_venue_title("Cruisery"), "The Cruisery")


if __name__ == "__main__":
    unittest.main()
