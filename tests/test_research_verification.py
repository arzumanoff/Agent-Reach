from agent_reach.research import EvidenceItem, EvidenceState, EvidenceStore, SourceKind
from agent_reach.research.report import build_summary
from agent_reach.research.verification import derive_state


def test_single_identifiable_source_is_single_source():
    item = EvidenceItem(source="github", source_id="commit:1", claim="claim")
    assert derive_state(item, EvidenceStore([item])) == EvidenceState.SINGLE_SOURCE


def test_independent_sources_raise_evidence_state():
    a = EvidenceItem(
        source="arxiv",
        source_id="paper:1",
        claim="support a",
        source_kind=SourceKind.PRIMARY,
    )
    b = EvidenceItem(source="reddit", source_id="thread:1", claim="support b")
    one = EvidenceItem(
        source="github",
        source_id="issue:1",
        claim="one",
        corroborates=(a.evidence_id,),
    )
    two = EvidenceItem(
        source="github",
        source_id="issue:2",
        claim="two",
        corroborates=(a.evidence_id, b.evidence_id),
    )
    store = EvidenceStore([one, two, a, b])
    assert derive_state(one, store) == EvidenceState.CORROBORATED
    assert derive_state(two, store) == EvidenceState.CONFIRMED


def test_two_secondary_sources_do_not_become_confirmed():
    a = EvidenceItem(source="news_a", canonical_url="https://a.example/x", claim="support")
    b = EvidenceItem(source="news_b", canonical_url="https://b.example/x", claim="support")
    target = EvidenceItem(
        source="community",
        canonical_url="https://c.example/x",
        claim="claim",
        corroborates=(a.evidence_id, b.evidence_id),
    )
    store = EvidenceStore([target, a, b])
    assert derive_state(target, store) == EvidenceState.CORROBORATED


def test_explicit_contradiction_is_visible():
    other = EvidenceItem(source="arxiv", source_id="paper:2", claim="opposite")
    item = EvidenceItem(
        source="github",
        source_id="issue:2",
        claim="claim",
        contradicts=(other.evidence_id,),
    )
    store = EvidenceStore([item, other])
    assert derive_state(item, store) == EvidenceState.CONTRADICTED


def test_summary_uses_derived_states():
    item = EvidenceItem(source="web", source_id="url:1", claim="claim")
    summary = build_summary(EvidenceStore([item]))
    assert summary["total"] == 1
    assert summary["single-source"] == 1
