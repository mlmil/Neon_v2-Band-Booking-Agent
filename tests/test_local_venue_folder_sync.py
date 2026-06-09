import tempfile
import unittest
from pathlib import Path

from scripts.local_venue_folder_sync import (
    LocalGig,
    build_local_model_prompt,
    gig_folder_name,
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


if __name__ == "__main__":
    unittest.main()
