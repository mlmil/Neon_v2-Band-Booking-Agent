#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path("/Volumes/VADER/Manifold/Neon_Blonde/Venues/_Logo Scout")
MAX_DOWNLOAD_BYTES = 2_000_000


@dataclass(frozen=True)
class VenueLogoCandidate:
    kind: str
    url: str
    source_url: str


class _LogoHTMLParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__()
        self.page_url = page_url
        self.candidates: list[VenueLogoCandidate] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "link":
            rel = attr.get("rel", "").lower()
            href = attr.get("href", "")
            if not href:
                return
            if "apple-touch-icon" in rel:
                self._append("apple_touch_icon", href)
            elif "icon" in rel:
                self._append("favicon", href)
        if tag.lower() == "meta":
            key = (attr.get("property") or attr.get("name") or "").lower()
            content = attr.get("content", "")
            if not content:
                return
            if key in {"og:image", "og:image:secure_url"}:
                self._append("og_image", content)
            elif key in {"twitter:image", "twitter:image:src"}:
                self._append("twitter_image", content)

    def _append(self, kind: str, href: str) -> None:
        self.candidates.append(
            VenueLogoCandidate(
                kind=kind,
                url=urllib.parse.urljoin(self.page_url, href),
                source_url=self.page_url,
            )
        )


def build_search_queries(venue: str, city: str) -> list[str]:
    base = f"{venue.strip()} {city.strip()}".strip()
    return [
        f"{base} official website",
        f"{base} logo",
        f"{base} Instagram",
    ]


def discover_logo_candidates(html: str, page_url: str) -> list[VenueLogoCandidate]:
    parser = _LogoHTMLParser(page_url)
    parser.feed(html)
    seen = set()
    unique = []
    for candidate in parser.candidates:
        key = (candidate.kind, candidate.url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def select_best_candidate(candidates: list[VenueLogoCandidate]) -> VenueLogoCandidate:
    priority = {
        "apple_touch_icon": 0,
        "og_image": 1,
        "twitter_image": 2,
        "favicon": 3,
    }
    return sorted(candidates, key=lambda candidate: priority.get(candidate.kind, 99))[0]


def build_logo_receipt(
    venue: str,
    city: str,
    candidate: VenueLogoCandidate,
    local_path: Path,
) -> dict:
    return {
        "status": "needs_approval",
        "venue": venue,
        "city": city,
        "candidate_kind": candidate.kind,
        "candidate_url": candidate.url,
        "source_url": candidate.source_url,
        "local_path": str(local_path),
        "wordpress_uploaded": False,
        "found_at": datetime.now().isoformat(timespec="seconds"),
        "approval_note": "Review before uploading to WordPress or attaching to a public show.",
    }


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "NeonV2 Venue Logo Scout")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    return re.sub(r"\s+", "-", cleaned).lower() or "venue"


def _extension_from_url_or_type(url: str, content_type: str) -> str:
    path_ext = Path(urllib.parse.urlparse(url).path).suffix
    if path_ext:
        return path_ext[:10]
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    return guessed or ".img"


def download_candidate(candidate: VenueLogoCandidate, output_dir: Path, venue: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(candidate.url)
    req.add_header("User-Agent", "NeonV2 Venue Logo Scout")
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError("Logo candidate exceeds download size limit")
    ext = _extension_from_url_or_type(candidate.url, content_type)
    path = output_dir / f"{_safe_name(venue)}-{candidate.kind}{ext}"
    path.write_bytes(data)
    return path


def scout_official_url(venue: str, city: str, url: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict:
    html = fetch_html(url)
    candidates = discover_logo_candidates(html, url)
    if not candidates:
        return {
            "status": "needs_review",
            "code": "NO_LOGO_CANDIDATES",
            "venue": venue,
            "city": city,
            "source_url": url,
            "search_queries": build_search_queries(venue, city),
        }
    best = select_best_candidate(candidates)
    local_path = download_candidate(best, output_root / _safe_name(venue), venue)
    receipt = build_logo_receipt(venue, city, best, local_path)
    receipt["candidate_count"] = len(candidates)
    receipt["search_queries"] = build_search_queries(venue, city)
    receipt_path = local_path.with_suffix(local_path.suffix + ".receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Scout an official venue URL for public logo/icon candidates.")
    parser.add_argument("--venue", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    args = parser.parse_args()
    try:
        result = scout_official_url(args.venue, args.city, args.url, Path(args.output_root))
    except (urllib.error.URLError, ValueError) as exc:
        result = {
            "status": "blocked",
            "code": "LOGO_SCOUT_FAILED",
            "venue": args.venue,
            "city": args.city,
            "source_url": args.url,
            "failure_reason": str(exc),
        }
        print(json.dumps(result, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
