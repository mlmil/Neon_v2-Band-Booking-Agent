import unittest

from scripts.wordpress_show_sync import (
    PublicShow,
    build_show_payload,
    content_disposition_filename,
    default_slug,
    format_show_title,
    guess_media_type,
    should_sync_show,
)


class WordPressShowSyncTests(unittest.TestCase):
    def test_format_show_title_uses_public_date_and_venue(self):
        show = PublicShow(venue="Ms Special", city="Goleta", start="2026-08-15T19:00:00-07:00")
        self.assertEqual(format_show_title(show), "August 15 Ms Special")

    def test_default_slug_uses_date_and_normalized_venue(self):
        show = PublicShow(venue="Fox Wine Co _Topa Topa", city="Santa Barbara", start="2026-09-12T16:00:00")
        self.assertEqual(default_slug(show), "september-12-fox-wine-co-topa-topa")

    def test_test_venue_is_blocked_from_wordpress_sync(self):
        show = PublicShow(venue="Club Bobaloo", city="Bakersfield", start="2026-10-07T19:00:00")
        result = should_sync_show(show)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["code"], "TEST_VENUE_BLOCKED")

    def test_build_show_payload_defaults_to_draft_and_public_fields(self):
        show = PublicShow(venue="Cruisery", city="Santa Barbara", start="2026-06-12T21:00:00")
        payload = build_show_payload(show, show_year_term_id=18, featured_media_id=483, menu_order=11)
        self.assertEqual(payload["title"], "June 12 Cruisery")
        self.assertEqual(payload["status"], "draft")
        self.assertEqual(payload["slug"], "june-12-cruisery")
        self.assertEqual(payload["featured_media"], 483)
        self.assertEqual(payload["show_year"], [18])
        self.assertEqual(payload["menu_order"], 11)
        self.assertIn("9pm - Santa Barbara", payload["content"])

    def test_build_show_payload_omits_featured_media_when_unknown(self):
        show = PublicShow(venue="New Venue", city="Ventura", start="2026-12-05T20:00:00")
        payload = build_show_payload(show, show_year_term_id=18)
        self.assertNotIn("featured_media", payload)

    def test_guess_media_type_handles_common_logo_files(self):
        self.assertEqual(guess_media_type("logo.png"), "image/png")
        self.assertEqual(guess_media_type("logo.jpg"), "image/jpeg")
        self.assertEqual(guess_media_type("logo.ico"), "image/vnd.microsoft.icon")

    def test_content_disposition_filename_sanitizes_spaces(self):
        self.assertEqual(
            content_disposition_filename("Leashless Brewing Logo.png"),
            'attachment; filename="leashless-brewing-logo.png"',
        )


if __name__ == "__main__":
    unittest.main()
