import sys
from types import SimpleNamespace

from agent_reach.channels.duckduckgo import DuckDuckGoSearchChannel


class FakeDDGS:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def text(self, query, **kwargs):
        assert query == "gpu pcb"
        assert kwargs["backend"] == "duckduckgo"
        assert kwargs["max_results"] == 2
        return [
            {"title": "A", "href": "https://a.example/x", "body": "first"},
            {"title": "B", "href": "https://b.example/y", "body": "second"},
        ]


def test_duckduckgo_search_normalizes_results(monkeypatch):
    monkeypatch.setitem(sys.modules, "ddgs", SimpleNamespace(DDGS=FakeDDGS))
    results = DuckDuckGoSearchChannel().search("gpu pcb", limit=2)
    assert results == [
        {"title": "A", "url": "https://a.example/x", "snippet": "first"},
        {"title": "B", "url": "https://b.example/y", "snippet": "second"},
    ]


def test_duckduckgo_search_rejects_empty_query():
    import pytest

    with pytest.raises(ValueError):
        DuckDuckGoSearchChannel().search("   ")
