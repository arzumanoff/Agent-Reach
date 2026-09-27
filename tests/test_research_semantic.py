import pytest

from agent_reach.research.models import EvidenceItem
from agent_reach.research.semantic import ClaimRelation, apply_relations, compare_pair


def test_semantic_boundary_accepts_explicit_relation():
    a = EvidenceItem(source="a", source_id="1", claim="32 GB")
    b = EvidenceItem(source="b", source_id="2", claim="thirty two gigabytes")
    assert compare_pair(a, b, lambda x, y: ClaimRelation.SUPPORTS) == ClaimRelation.SUPPORTS


def test_semantic_boundary_rejects_freeform_model_output():
    a = EvidenceItem(source="a", source_id="1", claim="a")
    b = EvidenceItem(source="b", source_id="2", claim="b")
    with pytest.raises(TypeError):
        compare_pair(a, b, lambda x, y: "probably")


def test_apply_relations_updates_graph_symmetrically():
    a = EvidenceItem(source="a", canonical_url="https://a.example/x", claim="32 GB")
    b = EvidenceItem(source="b", canonical_url="https://b.example/x", claim="thirty two gigabytes")
    store = apply_relations(
        __import__("agent_reach.research.store", fromlist=["EvidenceStore"]).EvidenceStore([a, b]),
        [(a.evidence_id, b.evidence_id, ClaimRelation.SUPPORTS)],
    )
    assert b.evidence_id in store.get(a.evidence_id).corroborates
    assert a.evidence_id in store.get(b.evidence_id).corroborates


def test_apply_relations_records_contradictions():
    from agent_reach.research.store import EvidenceStore

    a = EvidenceItem(source="a", source_id="1", claim="32 GB")
    b = EvidenceItem(source="b", source_id="2", claim="16 GB")
    store = apply_relations(
        EvidenceStore([a, b]),
        [(a.evidence_id, b.evidence_id, ClaimRelation.CONTRADICTS)],
    )
    assert b.evidence_id in store.get(a.evidence_id).contradicts
