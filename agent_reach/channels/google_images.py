"""Google image search via the official Custom Search JSON API."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .base import Channel

_API = "https://www.googleapis.com/customsearch/v1"
_MAX_BYTES = 2 * 1024 * 1024


class GoogleImagesChannel(Channel):
    name = "google_images"
    description = "Google Images via official Custom Search API"
    backends = ["Google Custom Search API"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        return False

    def check(self, config=None):
        self.active_backend = None
        if config is None or not config.get("google_api_key") or not config.get("google_cx"):
            return "off", "Requires google_api_key and google_cx"
        return "warn", "Credentials configured; doctor does not spend image-search quota"

    def search(self, query: str, config, limit: int = 5) -> list[dict[str, Any]]:
        key = config.get("google_api_key")
        cx = config.get("google_cx")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Google image search query must not be empty")
        if not key or not cx:
            raise ValueError("Google image search is not configured")

        limit = max(1, min(int(limit), 10))
        params = urllib.parse.urlencode(
            {
                "key": key,
                "cx": cx,
                "q": query.strip(),
                "searchType": "image",
                "num": limit,
                "safe": "active",
            }
        )
        request = urllib.request.Request(
            _API + "?" + params,
            headers={"User-Agent": "agent-reach/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read(_MAX_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Google image search HTTP {exc.code}") from None
        except urllib.error.URLError:
            raise ValueError("Google image search transport failure") from None

        if len(raw) > _MAX_BYTES:
            raise ValueError("Google image response exceeds safety limit")

        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Google image search returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Google image search returned a non-object response")

        items = data.get("items", [])
        if not isinstance(items, list):
            raise ValueError("Google image search returned invalid items")

        results: list[dict[str, Any]] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            image = item.get("image")
            image_data = image if isinstance(image, dict) else {}
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "context_url": image_data.get("contextLink", ""),
                    "mime": item.get("mime", ""),
                    "width": image_data.get("width"),
                    "height": image_data.get("height"),
                }
            )
        return results
