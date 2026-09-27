import pytest

from agent_reach.research.models import EvidenceItem
from agent_reach.research.semantic import ClaimRelation, compare_pair


def test_semantic_boundary_accepts_explicit_relation():
    a = EvidenceItem(source="a", source_id="1", claim="32 GB")
    b = EvidenceItem(source="b", source_id="2", claim="thirty two gigabytes")
    assert compare_pair(a, b, lambda x, y: ClaimRelation.SUPPORTS) == ClaimRelation.SUPPORTS


def test_semantic_boundary_rejects_freeform_model_output():
    a = EvidenceItem(source="a", source_id="1", claim="a")
    b = EvidenceItem(source="b", source_id="2", claim="b")
    with pytest.raises(TypeError):
        compare_pair(a, b, lambda x, y: "probably")
