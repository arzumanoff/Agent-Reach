from agent_reach.research.contradictions import link_contradictions
from agent_reach.research.models import EvidenceItem, EvidenceState
from agent_reach.research.store import EvidenceStore
from agent_reach.research.verification import derive_state


def test_contradiction_links_are_symmetric_and_drive_state():
    a = EvidenceItem(source="official", source_id="a", claim="32 GB")
    b = EvidenceItem(source="photo", source_id="b", claim="16 GB")
    store = link_contradictions(EvidenceStore([a, b]), [(a.evidence_id, b.evidence_id)])
    aa = store.get(a.evidence_id)
    bb = store.get(b.evidence_id)
    assert b.evidence_id in aa.contradicts
    assert a.evidence_id in bb.contradicts
    assert derive_state(aa, store) == EvidenceState.CONTRADICTED
