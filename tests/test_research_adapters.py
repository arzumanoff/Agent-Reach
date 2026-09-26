from agent_reach.research.adapters import evidence_from_result
from agent_reach.research.models import SourceKind


def test_arxiv_result_keeps_provenance():
    item = evidence_from_result(
        "arxiv",
        {
            "arxiv_id": "2601.12345",
            "title": "Paper",
            "authors": ["A", "B"],
            "summary": "Measured result",
            "link": "https://arxiv.org/abs/2601.12345",
            "published": "2026-01-01",
        },
        source_kind=SourceKind.PRIMARY,
    )
    assert item.source_id == "2601.12345"
    assert item.canonical_url == "https://arxiv.org/abs/2601.12345"
    assert item.author == "A, B"
    assert item.claim == "Measured result"


def test_hn_result_prefers_external_url_but_keeps_source_id():
    item = evidence_from_result(
        "hackernews",
        {"id": 42, "title": "Discussion", "url": "https://example.test/post", "snippet": "claim"},
        source_kind=SourceKind.COMMUNITY,
    )
    assert item.source_id == "42"
    assert item.canonical_url == "https://example.test/post"
