#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.venue_agent_tool import is_test_venue


WORDPRESS_BASE_URL = "https://neonblonde.band"
SHOW_ENDPOINT = "/wp-json/wp/v2/show"
MEDIA_ENDPOINT = "/wp-json/wp/v2/media"
DEFAULT_USER_AGENT = "NeonV2 Website Sync"


@dataclass(frozen=True)
class PublicShow:
    venue: str
    city: str
    start: str


def _start_dt(show: PublicShow) -> datetime:
    return datetime.fromisoformat(show.start.replace("Z", "+00:00"))


def _normalize_slug(value: str) -> str:
    lowered = value.lower().replace("&", " and ").replace("_", " ")
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered)
    return re.sub(r"-+", "-", cleaned).strip("-")


def _format_time(start: datetime) -> str:
    hour = start.hour
    minute = start.minute
    suffix = "am" if hour < 12 else "pm"
    display_hour = hour % 12 or 12
    if minute:
        return f"{display_hour}:{minute:02d}{suffix}"
    return f"{display_hour}{suffix}"


def guess_media_type(path_or_name: str) -> str:
    if path_or_name.lower().endswith(".ico"):
        return "image/vnd.microsoft.icon"
    guessed, _ = mimetypes.guess_type(path_or_name)
    if guessed:
        return guessed
    return "application/octet-stream"


def content_disposition_filename(path_or_name: str) -> str:
    name = Path(path_or_name).name.lower()
    name = re.sub(r"[^a-z0-9._-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return f'attachment; filename="{name or "logo.img"}"'


def format_show_title(show: PublicShow) -> str:
    start = _start_dt(show)
    date = start.strftime("%B ") + str(start.day)
    return f"{date} {show.venue.strip()}"


def default_slug(show: PublicShow) -> str:
    return _normalize_slug(format_show_title(show))


def should_sync_show(show: PublicShow) -> dict:
    if is_test_venue(show.venue):
        return {
            "allowed": False,
            "code": "TEST_VENUE_BLOCKED",
            "message": "Test venues never sync to public WordPress.",
        }
    if not show.venue.strip() or not show.city.strip():
        return {
            "allowed": False,
            "code": "PUBLIC_SHOW_INCOMPLETE",
            "message": "Venue and city are required for public WordPress sync.",
        }
    try:
        _start_dt(show)
    except ValueError:
        return {
            "allowed": False,
            "code": "PUBLIC_SHOW_INVALID_START",
            "message": "Start datetime is invalid.",
        }
    return {"allowed": True, "code": "PUBLIC_SHOW_READY"}


def build_show_payload(
    show: PublicShow,
    *,
    show_year_term_id: int,
    featured_media_id: int | None = None,
    menu_order: int | None = None,
    status: str = "draft",
) -> dict:
    start = _start_dt(show)
    payload: dict[str, Any] = {
        "title": format_show_title(show),
        "status": status,
        "slug": default_slug(show),
        "show_year": [show_year_term_id],
        "content": f"{_format_time(start)} - {show.city.strip()}",
    }
    if featured_media_id is not None:
        payload["featured_media"] = featured_media_id
    if menu_order is not None:
        payload["menu_order"] = menu_order
    return payload


class WordPressClient:
    def __init__(
        self,
        *,
        username: str,
        app_password: str,
        base_url: str = WORDPRESS_BASE_URL,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        token = base64.b64encode(f"{username}:{app_password}".encode("utf-8")).decode("ascii")
        self.authorization = f"Basic {token}"

    def request(self, method: str, endpoint: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}{endpoint}", data=data, method=method)
        req.add_header("Authorization", self.authorization)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", self.user_agent)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body[:500]}
            return exc.code, parsed

    def binary_request(
        self,
        method: str,
        endpoint: str,
        *,
        data: bytes,
        content_type: str,
        content_disposition: str,
    ) -> tuple[int, dict]:
        req = urllib.request.Request(f"{self.base_url}{endpoint}", data=data, method=method)
        req.add_header("Authorization", self.authorization)
        req.add_header("Content-Type", content_type)
        req.add_header("Content-Disposition", content_disposition)
        req.add_header("User-Agent", self.user_agent)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body[:500]}
            return exc.code, parsed

    def create_show(self, payload: dict) -> tuple[int, dict]:
        return self.request("POST", SHOW_ENDPOINT, payload)

    def read_show(self, post_id: int) -> tuple[int, dict]:
        return self.request("GET", f"{SHOW_ENDPOINT}/{post_id}?context=edit")

    def delete_show(self, post_id: int) -> tuple[int, dict]:
        return self.request("DELETE", f"{SHOW_ENDPOINT}/{post_id}?force=true")

    def upload_media_file(self, path: Path, *, title: str | None = None, alt_text: str | None = None) -> tuple[int, dict]:
        status, media = self.binary_request(
            "POST",
            MEDIA_ENDPOINT,
            data=path.read_bytes(),
            content_type=guess_media_type(path.name),
            content_disposition=content_disposition_filename(path.name),
        )
        if status not in (200, 201):
            return status, media
        updates = {}
        if title:
            updates["title"] = title
        if alt_text:
            updates["alt_text"] = alt_text
        if updates:
            update_status, updated = self.request("POST", f"{MEDIA_ENDPOINT}/{media['id']}", updates)
            return update_status, updated
        return status, media

    def read_media(self, media_id: int) -> tuple[int, dict]:
        return self.request("GET", f"{MEDIA_ENDPOINT}/{media_id}?context=edit")

    def delete_media(self, media_id: int) -> tuple[int, dict]:
        return self.request("DELETE", f"{MEDIA_ENDPOINT}/{media_id}?force=true")


def _args_to_show(args: argparse.Namespace) -> PublicShow:
    return PublicShow(venue=args.venue, city=args.city, start=args.start)


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft-only WordPress Show Sync tester.")
    parser.add_argument("--venue", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--show-year-term-id", type=int, required=True)
    parser.add_argument("--featured-media-id", type=int)
    parser.add_argument("--menu-order", type=int)
    parser.add_argument("--create-draft", action="store_true")
    parser.add_argument("--delete-after-read", action="store_true")
    parser.add_argument("--upload-media")
    parser.add_argument("--media-title")
    parser.add_argument("--media-alt-text")
    parser.add_argument("--delete-media-after-read", action="store_true")
    args = parser.parse_args()

    if args.upload_media:
        username = os.environ.get("NEON_WP_USERNAME")
        app_password = os.environ.get("NEON_WP_APP_PASSWORD")
        media_path = Path(args.upload_media)
        if not username or not app_password:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "code": "WORDPRESS_AUTH_MISSING",
                        "message": "Set NEON_WP_USERNAME and NEON_WP_APP_PASSWORD.",
                        "local_path": str(media_path),
                    },
                    indent=2,
                )
            )
            return 1
        if not media_path.exists():
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "code": "MEDIA_FILE_MISSING",
                        "local_path": str(media_path),
                    },
                    indent=2,
                )
            )
            return 1
        client = WordPressClient(username=username, app_password=app_password)
        upload_status, uploaded = client.upload_media_file(
            media_path,
            title=args.media_title,
            alt_text=args.media_alt_text,
        )
        receipt = {
            "status": "uploaded" if upload_status in (200, 201) else "blocked",
            "upload_status": upload_status,
            "local_path": str(media_path),
        }
        if upload_status not in (200, 201):
            receipt["error"] = uploaded
            print(json.dumps(receipt, indent=2))
            return 1
        media_id = uploaded["id"]
        read_status, readback = client.read_media(media_id)
        receipt.update(
            {
                "media_id": media_id,
                "source_url": uploaded.get("source_url"),
                "read_status": read_status,
                "read_title": readback.get("title", {}).get("rendered"),
            }
        )
        if args.delete_media_after_read:
            delete_status, deleted = client.delete_media(media_id)
            receipt["delete_status"] = delete_status
            receipt["deleted"] = deleted.get("deleted")
        print(json.dumps(receipt, indent=2))
        return 0

    show = _args_to_show(args)
    gate = should_sync_show(show)
    if not gate["allowed"]:
        print(json.dumps({"status": "blocked", **gate}, indent=2))
        return 1

    payload = build_show_payload(
        show,
        show_year_term_id=args.show_year_term_id,
        featured_media_id=args.featured_media_id,
        menu_order=args.menu_order,
    )
    if not args.create_draft:
        print(json.dumps({"status": "dry_run", "payload": payload}, indent=2))
        return 0

    username = os.environ.get("NEON_WP_USERNAME")
    app_password = os.environ.get("NEON_WP_APP_PASSWORD")
    if not username or not app_password:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "code": "WORDPRESS_AUTH_MISSING",
                    "message": "Set NEON_WP_USERNAME and NEON_WP_APP_PASSWORD.",
                    "payload": payload,
                },
                indent=2,
            )
        )
        return 1

    client = WordPressClient(username=username, app_password=app_password)
    create_status, created = client.create_show(payload)
    receipt = {"status": "created" if create_status in (200, 201) else "blocked", "create_status": create_status}
    if create_status not in (200, 201):
        receipt["error"] = created
        print(json.dumps(receipt, indent=2))
        return 1

    post_id = created["id"]
    read_status, readback = client.read_show(post_id)
    receipt.update(
        {
            "post_id": post_id,
            "post_status": created.get("status"),
            "link": created.get("link"),
            "read_status": read_status,
            "read_title": readback.get("title", {}).get("rendered"),
        }
    )
    if args.delete_after_read:
        delete_status, deleted = client.delete_show(post_id)
        receipt["delete_status"] = delete_status
        receipt["deleted"] = deleted.get("deleted")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
