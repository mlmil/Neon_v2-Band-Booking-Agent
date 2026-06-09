import tempfile
import unittest
from pathlib import Path

from scripts.venue_logo_scout import (
    VenueLogoCandidate,
    build_logo_receipt,
    build_search_queries,
    discover_logo_candidates,
    select_best_candidate,
)


class VenueLogoScoutTests(unittest.TestCase):
    def test_build_search_queries_prefers_official_sources(self):
        queries = build_search_queries("Leashless Brewing", "Ventura")
        self.assertEqual(queries[0], "Leashless Brewing Ventura official website")
        self.assertIn("Leashless Brewing Ventura logo", queries)

    def test_discover_logo_candidates_reads_icon_and_open_graph_images(self):
        html = """
        <html><head>
          <link rel="icon" href="/favicon.ico">
          <link rel="apple-touch-icon" href="/apple-touch-icon.png">
          <meta property="og:image" content="https://example.com/social-logo.png">
        </head></html>
        """
        candidates = discover_logo_candidates(html, "https://example.com/shows")
        urls = [candidate.url for candidate in candidates]
        self.assertIn("https://example.com/favicon.ico", urls)
        self.assertIn("https://example.com/apple-touch-icon.png", urls)
        self.assertIn("https://example.com/social-logo.png", urls)

    def test_select_best_candidate_prefers_touch_icon_over_social_image(self):
        candidates = [
            VenueLogoCandidate(kind="og_image", url="https://example.com/og.jpg", source_url="https://example.com"),
            VenueLogoCandidate(kind="apple_touch_icon", url="https://example.com/icon.png", source_url="https://example.com"),
        ]
        self.assertEqual(select_best_candidate(candidates).url, "https://example.com/icon.png")

    def test_select_best_candidate_prefers_social_image_over_favicon(self):
        candidates = [
            VenueLogoCandidate(kind="favicon", url="https://example.com/favicon.ico", source_url="https://example.com"),
            VenueLogoCandidate(kind="og_image", url="https://example.com/logo.png", source_url="https://example.com"),
        ]
        self.assertEqual(select_best_candidate(candidates).url, "https://example.com/logo.png")

    def test_build_logo_receipt_records_source_and_local_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logo.png"
            path.write_bytes(b"fake")
            candidate = VenueLogoCandidate(
                kind="favicon",
                url="https://example.com/favicon.ico",
                source_url="https://example.com",
            )
            receipt = build_logo_receipt("Example Room", "Ventura", candidate, path)
            self.assertEqual(receipt["status"], "needs_approval")
            self.assertEqual(receipt["venue"], "Example Room")
            self.assertEqual(receipt["city"], "Ventura")
            self.assertEqual(receipt["candidate_url"], "https://example.com/favicon.ico")
            self.assertEqual(receipt["local_path"], str(path))
            self.assertFalse(receipt["wordpress_uploaded"])


if __name__ == "__main__":
    unittest.main()
