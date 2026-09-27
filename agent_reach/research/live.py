"""First-class adapters from Agent-Reach channels to ResearchRun search callables."""

from __future__ import annotations

import importlib.util
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
from .runner import ResearchRun, SearchFn
from .policy import PolicyResult


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


def build_live_searches(
    config: Config | None = None,
) -> tuple[dict[str, SearchFn], dict[str, SourceKind]]:
    """Build the safe structured search set available in the current environment."""
    cfg = config or Config(read_only=True)
    searches: dict[str, SearchFn] = {
        "arxiv": arxiv_search(),
        "hackernews": hackernews_search(),
    }
    kinds: dict[str, SourceKind] = {
        "arxiv": SourceKind.PRIMARY,
        "hackernews": SourceKind.COMMUNITY,
    }

    if cfg.get("exa_api_key"):
        searches["exa"] = exa_rest_search(cfg)
        kinds["exa"] = SourceKind.SECONDARY

    if cfg.get("google_api_key") and cfg.get("google_cx"):
        searches["google_images"] = google_images_search(cfg)
        kinds["google_images"] = SourceKind.SECONDARY

    if importlib.util.find_spec("ddgs") is not None:
        searches["duckduckgo"] = duckduckgo_search()
        kinds["duckduckgo"] = SourceKind.SECONDARY

    return searches, kinds


def execute_live_research(
    plan: ResearchPlan,
    config: Config | None = None,
) -> tuple[ResearchRun, PolicyResult, str]:
    """Execute a plan against currently available structured research backends."""
    searches, kinds = build_live_searches(config)
    return execute_research(plan, searches, kinds)
