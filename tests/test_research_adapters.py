from agent_reach.research.adapters import evidence_from_result
from agent_reach.research.artifacts import ArtifactKind
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
        {"id": 42, "title": "Discussion", "url": "https://example.test/post", "hn_url": "https://news.ycombinator.com/item?id=42", "snippet": "claim"},
        source_kind=SourceKind.COMMUNITY,
    )
    assert item.source_id == "42"
    assert item.canonical_url == "https://news.ycombinator.com/item?id=42"
    assert item.metadata["external_url"] == "https://example.test/post"
    assert item.artifact_refs[0].kind == ArtifactKind.THREAD


def test_exa_highlights_become_claim_when_text_is_absent():
    item = evidence_from_result(
        "exa",
        {"url": "https://example.test", "title": "Page", "highlights": ["First fact", "Second fact"]},
    )
    assert item.claim == "First fact Second fact"


def test_image_context_url_is_used_when_image_url_missing():
    item = evidence_from_result(
        "google_images",
        {"title": "PCB", "context_url": "https://vendor.example/board"},
    )
    assert item.canonical_url == "https://vendor.example/board"
    assert item.artifact_refs[0].kind == ArtifactKind.IMAGE


def test_google_image_prefers_context_page_for_provenance():
    item = evidence_from_result(
        "google_images",
        {
            "title": "PCB",
            "url": "https://cdn.example/pcb.jpg",
            "context_url": "https://vendor.example/board",
        },
    )
    assert item.canonical_url == "https://vendor.example/board"
    assert item.metadata["artifact_url"] == "https://cdn.example/pcb.jpg"


def test_adapter_scrubs_url_credentials():
    item = evidence_from_result(
        "web",
        {"title": "Page", "text": "claim", "url": "https://u:p@example.test/x?token=secret"},
    )
    assert "secret" not in item.canonical_url
    assert "u:p" not in item.canonical_url


def test_arxiv_result_emits_document_artifact():
    item = evidence_from_result(
        "arxiv",
        {
            "arxiv_id": "2601.12345",
            "title": "Paper",
            "summary": "Measured result",
            "link": "https://arxiv.org/abs/2601.12345",
        },
        source_kind=SourceKind.PRIMARY,
    )
    assert item.artifact_refs[0].kind == ArtifactKind.DOCUMENT
