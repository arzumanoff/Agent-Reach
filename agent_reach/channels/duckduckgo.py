"""DuckDuckGo text search via the maintained ddgs package."""

from __future__ import annotations

import importlib.util
from typing import Any

from .base import Channel


class DuckDuckGoSearchChannel(Channel):
    name = "duckduckgo"
    description = "DuckDuckGo text search via ddgs"
    backends = ["DDGS (DuckDuckGo)"]
    tier = 1

    def can_handle(self, url: str) -> bool:
        return False

    def check(self, config=None):
        self.active_backend = None
        if importlib.util.find_spec("ddgs") is None:
            return "off", "Optional search backend not installed: pip install -U ddgs"
        return (
            "warn",
            "ddgs is installed; Doctor does not issue a live search. "
            "The first read-only query verifies network availability.",
        )

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("DuckDuckGo query must not be empty")
        limit = max(1, min(int(limit), 50))

        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise RuntimeError("ddgs is not installed; run: pip install -U ddgs") from exc

        try:
            raw_results = DDGS(timeout=10).text(
                query.strip(),
                max_results=limit,
                safesearch="moderate",
                backend="duckduckgo",
            )
        except Exception as exc:
            raise RuntimeError(
                f"DuckDuckGo search failed: {type(exc).__name__}"
            ) from None

        if not isinstance(raw_results, list):
            raise ValueError("DuckDuckGo returned an invalid result list")

        results: list[dict[str, Any]] = []
        for raw in raw_results[:limit]:
            if not isinstance(raw, dict):
                continue
            url = raw.get("href") or raw.get("url") or ""
            title = raw.get("title") or ""
            body = raw.get("body") or raw.get("snippet") or ""
            if not url and not body and not title:
                continue
            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": body,
                }
            )
        return results
