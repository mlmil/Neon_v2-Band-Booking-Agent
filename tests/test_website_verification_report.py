import unittest

from scripts.website_verification_report import (
    add_cache_buster,
    compare_website_to_bandsheet,
    find_hosted_widget_src,
    parse_rendered_show_cards,
    parse_wordpress_show,
)


class WebsiteVerificationReportTests(unittest.TestCase):
    def test_parse_wordpress_show_title(self):
        post = {
            "id": 660,
            "link": "https://neonblonde.band/show/june-12-cruisery/",
            "title": {"rendered": "June 12 Cruisery"},
        }
        self.assertEqual(
            parse_wordpress_show(post),
            {
                "date": "2026-06-12",
                "venue": "Cruisery",
                "id": 660,
                "title": "June 12 Cruisery",
                "link": "https://neonblonde.band/show/june-12-cruisery/",
            },
        )

    def test_compare_flags_wrong_website_venue_on_same_date(self):
        bandsheet = [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}]
        website = [{"date": "2026-07-18", "venue": "Leashless", "id": 618, "title": "July 18 Leashless"}]
        result = compare_website_to_bandsheet(bandsheet, website)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["code"], "WEBSITE_MISMATCH")
        self.assertEqual(result["mismatches"][0]["type"], "bandsheet_missing_or_different_on_website")

    def test_compare_accepts_punctuation_only_differences(self):
        bandsheet = [{"date": "2026-09-06", "venue": "Jeffs Wedding", "city": "Nipomo", "time": "7pm"}]
        website = [{"date": "2026-09-06", "venue": "Jeff’s Wedding", "id": 631, "title": "Sept 6 Jeff’s Wedding"}]
        result = compare_website_to_bandsheet(bandsheet, website)
        self.assertEqual(result["status"], "success")

    def test_compare_accepts_private_party_public_alias(self):
        bandsheet = [{"date": "2026-08-01", "venue": "Private Party for Vickie", "city": "Ventura", "time": "7pm"}]
        website = [{"date": "2026-08-01", "venue": "Private Gig", "id": 619, "title": "August 1 Private Gig"}]
        result = compare_website_to_bandsheet(bandsheet, website)
        self.assertEqual(result["status"], "success")

    def test_compare_flags_rendered_city_mismatch(self):
        bandsheet = [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Santa Barbara", "time": "6pm"}]
        website = [{"date": "2026-07-18", "venue": "Santa Barbara Yacht Club", "city": "Ventura", "time": "6pm"}]
        result = compare_website_to_bandsheet(bandsheet, website)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["mismatches"][0]["type"], "city_mismatch")

    def test_compare_accepts_rendered_city_detail(self):
        bandsheet = [{"date": "2026-09-12", "venue": "Fox Wine Co _Topa Topa", "city": "Santa Barbara", "time": "4pm"}]
        website = [{"date": "2026-09-12", "venue": "Fox Wine Co. & Topa Topa", "city": "Santa Barbara: Funk Zone", "time": "4pm"}]
        result = compare_website_to_bandsheet(bandsheet, website)
        self.assertEqual(result["status"], "success")

    def test_parse_rendered_show_cards(self):
        page = """
        <h2 class="x-text-content-text-primary">Upcoming Shows</h2>
        <span class="x-text-content-text-primary">July 18</span>
        <span class="x-text-content-text-primary">Santa Barbara Yacht Club</span>
        <span class="x-text-content-text-subheadline">6pm - Santa Barbara</span>
        <span class="x-text-content-text-primary">August 9</span>
        <span class="x-text-content-text-primary">Leashless Brewing</span>
        <span class="x-text-content-text-subheadline">3pm - Ventura</span>
        <h2 class="x-text-content-text-primary">Now Booking</h2>
        """
        self.assertEqual(
            parse_rendered_show_cards(page),
            [
                {
                    "date": "2026-07-18",
                    "venue": "Santa Barbara Yacht Club",
                    "city": "Santa Barbara",
                    "time": "6pm",
                    "title": "July 18 Santa Barbara Yacht Club",
                    "source": "rendered_page",
                },
                {
                    "date": "2026-08-09",
                    "venue": "Leashless Brewing",
                    "city": "Ventura",
                    "time": "3pm",
                    "title": "August 9 Leashless Brewing",
                    "source": "rendered_page",
                },
            ],
        )

    def test_find_hosted_widget_src(self):
        page = """
        <main>
          <iframe src="https://mlmil.github.io/NeonBlonde-Bandsheet/docs/public-shows-widget.html?v=20260616-1718"></iframe>
        </main>
        """
        self.assertEqual(
            find_hosted_widget_src(page),
            "https://mlmil.github.io/NeonBlonde-Bandsheet/docs/public-shows-widget.html?v=20260616-1718",
        )

    def test_add_cache_buster_preserves_existing_query(self):
        self.assertEqual(
            add_cache_buster("https://neonblonde.band/wp-json/wp/v2/show?per_page=100", token="abc"),
            "https://neonblonde.band/wp-json/wp/v2/show?per_page=100&_cb=abc",
        )


if __name__ == "__main__":
    unittest.main()
