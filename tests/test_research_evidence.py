from agent_reach.research import EvidenceItem, EvidenceState, EvidenceStore, SourceKind


def test_evidence_id_is_stable_across_whitespace_and_case():
    a = EvidenceItem(source="github", canonical_url="https://example.test/a", claim="VRAM is 32 GB")
    b = EvidenceItem(source="github", canonical_url="https://example.test/a", claim="  vram   IS 32 gb ")
    assert a.evidence_id == b.evidence_id


def test_store_deduplicates_same_evidence():
    item = EvidenceItem(
        source="arxiv",
        source_id="paper:123",
        claim="A measured result",
        source_kind=SourceKind.PRIMARY,
        state=EvidenceState.SINGLE_SOURCE,
    )
    store = EvidenceStore([item, item])
    assert len(store) == 1
    assert store.get(item.evidence_id) == item


def test_store_groups_sources():
    store = EvidenceStore(
        [
            EvidenceItem(source="github", source_id="1", claim="one"),
            EvidenceItem(source="github", source_id="2", claim="two"),
            EvidenceItem(source="reddit", source_id="3", claim="three"),
        ]
    )
    grouped = store.by_source()
    assert len(grouped["github"]) == 2
    assert len(grouped["reddit"]) == 1


def test_empty_claim_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        EvidenceItem(source="web", claim="   ")


def test_identity_normalization_keeps_id_stable():
    a = EvidenceItem(source="web", canonical_url="HTTPS://EXAMPLE.TEST/a", claim="Fact")
    b = EvidenceItem(source="web", canonical_url="https://example.test/a", claim=" fact ")
    assert a.evidence_id == b.evidence_id


def test_url_path_case_remains_significant():
    a = EvidenceItem(source="web", canonical_url="https://example.test/A", claim="Fact")
    b = EvidenceItem(source="web", canonical_url="https://example.test/a", claim="Fact")
    assert a.evidence_id != b.evidence_id


def test_store_iteration_is_deterministic_by_evidence_id():
    a = EvidenceItem(source="web", source_id="z", claim="z")
    b = EvidenceItem(source="web", source_id="a", claim="a")
    store = EvidenceStore([a, b])
    assert [item.evidence_id for item in store.all()] == sorted([a.evidence_id, b.evidence_id])
