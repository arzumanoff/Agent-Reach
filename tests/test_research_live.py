from agent_reach.research.live import DEFAULT_SOURCE_KINDS, arxiv_search, hackernews_search


class Arxiv:
    def search(self, query, limit=10):
        return [{"title": query, "limit": limit}]


class HN:
    def search(self, query, limit=10):
        return [{"title": query, "limit": limit}]


def test_arxiv_adapter_matches_runner_contract():
    assert arxiv_search(Arxiv())("paper", 3)[0]["limit"] == 3


def test_hn_adapter_matches_runner_contract():
    assert hackernews_search(HN())("agent", 4)[0]["limit"] == 4


def test_default_source_kinds_are_conservative():
    from agent_reach.research.models import SourceKind

    assert DEFAULT_SOURCE_KINDS["arxiv"] == SourceKind.PRIMARY
    assert DEFAULT_SOURCE_KINDS["hackernews"] == SourceKind.COMMUNITY
    assert DEFAULT_SOURCE_KINDS["duckduckgo"] == SourceKind.SECONDARY
    assert DEFAULT_SOURCE_KINDS["exa"] == SourceKind.SECONDARY
    assert DEFAULT_SOURCE_KINDS["google_images"] == SourceKind.SECONDARY


class Config:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key, default=None):
        return self.values.get(key, default)


def test_build_live_sources_includes_zero_config_sources(monkeypatch):
    monkeypatch.setattr(
        "agent_reach.research.live.DuckDuckGoSearchChannel.check",
        lambda self, config=None: ("off", "missing"),
    )
    searches, kinds = build_live_sources(Config())
    assert "arxiv" in searches
    assert "hackernews" in searches
    assert "exa" not in searches
    assert "google_images" not in searches
    assert kinds["arxiv"].value == "primary"


def test_build_live_sources_adds_configured_optional_sources(monkeypatch):
    monkeypatch.setattr(
        "agent_reach.research.live.DuckDuckGoSearchChannel.check",
        lambda self, config=None: ("warn", "installed"),
    )
    config = Config(
        {
            "exa_api_key": "exa",
            "google_api_key": "google",
            "google_cx": "cx",
        }
    )
    searches, kinds = build_live_sources(config)
    assert {"arxiv", "hackernews", "duckduckgo", "exa", "google_images"} <= set(searches)
    assert kinds["duckduckgo"].value == "secondary"
