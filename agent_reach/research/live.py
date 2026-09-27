"""First-class adapters from Agent-Reach channels to ResearchRun search callables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agent_reach.channels.arxiv import ArxivChannel
from agent_reach.channels.google_images import GoogleImagesChannel
from agent_reach.channels.hackernews import HackerNewsChannel
from agent_reach.config import Config

from .runner import SearchFn


def arxiv_search(channel: ArxivChannel | None = None) -> SearchFn:
    ch = channel or ArxivChannel()
    return lambda query, limit: ch.search(query, limit=limit)


def hackernews_search(channel: HackerNewsChannel | None = None) -> SearchFn:
    ch = channel or HackerNewsChannel()
    return lambda query, limit: ch.search(query, limit=limit)


def google_images_search(
    config: Config,
    channel: GoogleImagesChannel | None = None,
) -> SearchFn:
    ch = channel or GoogleImagesChannel()
    return lambda query, limit: ch.search(query, config, limit=limit)


def exa_rest_search(config: Config) -> SearchFn:
    def search(query: str, limit: int) -> Sequence[Mapping[str, Any]]:
        from agent_reach import exa_api

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Exa search query must not be empty")
        limit = max(1, min(int(limit), 100))
        key = exa_api.require_api_key(config)
        payload = {
            "query": query.strip(),
            "type": "auto",
            "numResults": limit,
            "contents": {"highlights": True},
        }
        body = exa_api.request_json("search", payload, api_key=key)
        results = body.get("results")
        if not isinstance(results, list):
            return []
        return [item for item in results if isinstance(item, Mapping)]

    return search
