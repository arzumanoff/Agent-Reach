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
from .orchestrator import execute_research
from .planner import ResearchPlan
from .policy import PolicyResult
from .runner import ResearchRun, SearchFn

DEFAULT_SOURCE_KINDS: dict[str, SourceKind] = {
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

        key = exa_api.require_api_key(config)
        payload = {
            "query": query.strip(),
            "type": "auto",
            "numResults": max(1, min(int(limit), 100)),
            "contents": {"highlights": True},
        }
        body = exa_api.request_json("search", payload, api_key=key)
        results = body.get("results")
        return results if isinstance(results, list) else []

    return search


def duckduckgo_search(
    channel: DuckDuckGoSearchChannel | None = None,
) -> SearchFn:
    ch = channel or DuckDuckGoSearchChannel()
    return lambda query, limit: ch.search(query, limit=limit)


def build_live_sources(
    config: Config | None = None,
) -> tuple[dict[str, SearchFn], dict[str, SourceKind]]:
    """Build structured sources that are usable or explicitly configured now."""
    cfg = config or Config(read_only=True)
    searches: dict[str, SearchFn] = {
        "arxiv": arxiv_search(),
        "hackernews": hackernews_search(),
    }

    if cfg.get("exa_api_key"):
        searches["exa"] = exa_rest_search(cfg)

    if cfg.get("google_api_key") and cfg.get("google_cx"):
        searches["google_images"] = google_images_search(cfg)

    ddg_channel = DuckDuckGoSearchChannel()
    ddg_status, _message = ddg_channel.check(cfg)
    if ddg_status in {"ok", "warn"}:
        searches["duckduckgo"] = duckduckgo_search(ddg_channel)

    kinds = {
        source: DEFAULT_SOURCE_KINDS[source]
        for source in searches
        if source in DEFAULT_SOURCE_KINDS
    }
    return searches, kinds


def build_live_searches(
    config: Config | None = None,
) -> tuple[dict[str, SearchFn], dict[str, SourceKind]]:
    """Backward-compatible alias for :func:`build_live_sources`."""
    return build_live_sources(config)


def execute_live_research(
    plan: ResearchPlan,
    config: Config | None = None,
) -> tuple[ResearchRun, PolicyResult, str]:
    """Execute a plan against currently available structured research backends."""
    searches, kinds = build_live_sources(config)
    return execute_research(plan, searches, kinds)
