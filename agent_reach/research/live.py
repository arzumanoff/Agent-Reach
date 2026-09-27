"""First-class adapters from Agent-Reach channels to ResearchRun search callables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agent_reach.channels.arxiv import ArxivChannel
from agent_reach.channels.duckduckgo import DuckDuckGoSearchChannel
from agent_reach.channels.google_images import GoogleImagesChannel
from agent_reach.channels.hackernews import HackerNewsChannel
from agent_reach.config import Config

from .models import SourceKind
from .runner import SearchFn

DEFAULT_SOURCE_KINDS = {
    "arxiv": SourceKind.PRIMARY,
    "hackernews": SourceKind.COMMUNITY,
    "duckduckgo": SourceKind.SECONDARY,
    "exa": SourceKind.SECONDARY,
    "google_images": SourceKind.SECONDARY,
}


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


def duckduckgo_search(
    channel: DuckDuckGoSearchChannel | None = None,
) -> SearchFn:
    ch = channel or DuckDuckGoSearchChannel()
    return lambda query, limit: ch.search(query, limit=limit)


def build_live_sources(
    config: Config,
) -> tuple[dict[str, SearchFn], dict[str, SourceKind]]:
    """Build the live search registry from locally available/configured backends."""
    searches: dict[str, SearchFn] = {
        "arxiv": arxiv_search(),
        "hackernews": hackernews_search(),
    }

    if DuckDuckGoSearchChannel().check(config)[0] != "off":
        searches["duckduckgo"] = duckduckgo_search()

    if config.get("exa_api_key"):
        searches["exa"] = exa_rest_search(config)

    if config.get("google_api_key") and config.get("google_cx"):
        searches["google_images"] = google_images_search(config)

    source_kinds = {
        source: DEFAULT_SOURCE_KINDS[source]
        for source in searches
    }
    return searches, source_kinds
