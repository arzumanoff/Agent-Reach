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
