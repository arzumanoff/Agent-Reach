from agent_reach.research.corroboration import link_exact_claims
from agent_reach.research.models import EvidenceItem, EvidenceState
from agent_reach.research.store import EvidenceStore
from agent_reach.research.verification import derive_state


def test_exact_claims_from_independent_sources_are_linked():
    a = EvidenceItem(source="github", source_id="1", claim="Memory is 32 GB")
    b = EvidenceItem(source="arxiv", source_id="2", claim=" memory   IS 32 gb ")
    linked = link_exact_claims(EvidenceStore([a, b]))
    aa = linked.get(a.evidence_id)
    assert aa is not None
    assert b.evidence_id in aa.corroborates
    assert derive_state(aa, linked) == EvidenceState.CORROBORATED


def test_same_source_does_not_self_corroborate():
    a = EvidenceItem(source="web", source_id="1", claim="same")
    b = EvidenceItem(source="web", source_id="2", claim="same")
    linked = link_exact_claims(EvidenceStore([a, b]))
    assert linked.get(a.evidence_id).corroborates == ()
