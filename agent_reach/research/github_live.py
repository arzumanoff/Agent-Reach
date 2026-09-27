"""Read-only GitHub repository discovery for Research Edition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import requests

from agent_reach.config import Config

_API = "https://api.github.com/search/repositories"
_TIMEOUT = 20


def github_repository_search(config: Config):
    def search(query: str, limit: int) -> Sequence[Mapping[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("GitHub search query must not be empty")

        per_page = max(1, min(int(limit), 30))
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "agent-reach-research",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = config.get("github_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.get(
                _API,
                params={
                    "q": query.strip(),
                    "per_page": per_page,
                    "sort": "stars",
                    "order": "desc",
                },
                headers=headers,
                timeout=_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"GitHub search transport failure: {type(exc).__name__}"
            ) from None

        if not response.ok:
            raise RuntimeError(f"GitHub search HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("GitHub search returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("GitHub search returned a non-object response")

        items = payload.get("items", [])
        if not isinstance(items, list):
            raise ValueError("GitHub search returned invalid items")

        results: list[dict[str, Any]] = []
        for item in items[:per_page]:
            if not isinstance(item, dict):
                continue
            full_name = item.get("full_name") or item.get("name") or ""
            url = item.get("html_url") or ""
            description = item.get("description") or ""
            if not full_name and not url:
                continue
            results.append(
                {
                    "id": item.get("id"),
                    "title": full_name,
                    "url": url,
                    "snippet": description or full_name,
                    "author": (item.get("owner") or {}).get("login")
                    if isinstance(item.get("owner"), dict)
                    else "",
                    "stars": item.get("stargazers_count"),
                    "updated_at": item.get("updated_at"),
                }
            )
        return results

    return search
