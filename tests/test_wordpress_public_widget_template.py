from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "WORDPRESS_PUBLIC_SHOWS_WIDGET.html"


class WordPressPublicWidgetTemplateTests(unittest.TestCase):
    def test_template_uses_public_bandsheet_feed(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("bandsheet-data.json", source)
        self.assertIn("booked_gigs", source)
        self.assertIn("club babaloo|club bobaloo", source)

    def test_template_does_not_cap_public_show_count(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn(".slice(0, 12)", source)

    def test_template_uses_known_venue_images(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("SB_Yacht_Club.png", source)
        self.assertIn("MSpecial.png", source)
        self.assertIn("tonys-pizzaria-logo.png", source)


if __name__ == "__main__":
    unittest.main()
