from agent_reach.research.models import EvidenceItem, SourceKind
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.policy import evaluate_policy
from agent_reach.research.store import EvidenceStore


def test_policy_requires_source_diversity():
    plan = ResearchPlan(topic="x", questions=(ResearchQuestion("q"),), minimum_independent_sources=2)
    result = evaluate_policy(plan, EvidenceStore([EvidenceItem(source="web", source_id="1", claim="x")]))
    assert result.satisfied is False
    assert result.independent_sources == 1


def test_policy_can_require_primary_source():
    plan = ResearchPlan(
        topic="x",
        questions=(ResearchQuestion("q", require_primary_source=True),),
        minimum_independent_sources=1,
    )
    result = evaluate_policy(
        plan,
        EvidenceStore([EvidenceItem(source="arxiv", source_id="1", claim="x", source_kind=SourceKind.PRIMARY)]),
    )
    assert result.satisfied is True
    assert result.primary_sources == 1


def test_two_urls_found_through_same_transport_count_as_two_publishers():
    plan = ResearchPlan(topic="x", questions=(ResearchQuestion("q"),), minimum_independent_sources=2)
    store = EvidenceStore([
        EvidenceItem(source="exa", canonical_url="https://vendor.example/spec", claim="x"),
        EvidenceItem(source="exa", canonical_url="https://lab.example/test", claim="x"),
    ])
    assert evaluate_policy(plan, store).satisfied is True


def test_same_publisher_via_two_channels_counts_once():
    plan = ResearchPlan(topic="x", questions=(ResearchQuestion("q"),), minimum_independent_sources=2)
    store = EvidenceStore([
        EvidenceItem(source="exa", canonical_url="https://vendor.example/spec", claim="x"),
        EvidenceItem(source="web", canonical_url="https://vendor.example/news", claim="x"),
    ])
    result = evaluate_policy(plan, store)
    assert result.satisfied is False
    assert result.independent_sources == 1


def test_two_records_from_same_channel_without_urls_count_once():
    plan = ResearchPlan(topic="x", questions=(ResearchQuestion("q"),), minimum_independent_sources=2)
    store = EvidenceStore([
        EvidenceItem(source="reddit", source_id="thread:1", claim="x"),
        EvidenceItem(source="reddit", source_id="thread:2", claim="x"),
    ])
    result = evaluate_policy(plan, store)
    assert result.independent_sources == 1
    assert result.satisfied is False


def test_primary_requirement_is_checked_per_question():
    plan = ResearchPlan(
        topic="two questions",
        questions=(
            ResearchQuestion("q1", ("arxiv",), require_primary_source=True),
            ResearchQuestion("q2", ("reddit",), require_primary_source=True),
        ),
        minimum_independent_sources=1,
    )
    primary = EvidenceItem(
        source="arxiv",
        source_id="paper:1",
        claim="primary",
        source_kind=SourceKind.PRIMARY,
    )
    community = EvidenceItem(
        source="reddit",
        source_id="thread:1",
        claim="community",
        source_kind=SourceKind.COMMUNITY,
    )
    store = EvidenceStore([primary, community])
    result = evaluate_policy(
        plan,
        store,
        {
            "q1": {primary.evidence_id},
            "q2": {community.evidence_id},
        },
    )
    assert result.satisfied is False
    assert "question 'q2' requires primary-source evidence" in result.reasons


def test_source_diversity_is_checked_per_question():
    plan = ResearchPlan(
        topic="two questions",
        questions=(
            ResearchQuestion("q1", ("a", "b")),
            ResearchQuestion("q2", ("c",)),
        ),
        minimum_independent_sources=2,
    )
    a = EvidenceItem(source="a", canonical_url="https://a.example/x", claim="a")
    b = EvidenceItem(source="b", canonical_url="https://b.example/x", claim="b")
    c = EvidenceItem(source="c", canonical_url="https://c.example/x", claim="c")
    store = EvidenceStore([a, b, c])
    result = evaluate_policy(
        plan,
        store,
        {
            "q1": {a.evidence_id, b.evidence_id},
            "q2": {c.evidence_id},
        },
    )
    assert result.satisfied is False
    assert "question 'q2' needs 2 independent sources; have 1" in result.reasons


def test_publisher_id_override_unifies_mirrors():
    plan = ResearchPlan(
        topic="x",
        questions=(ResearchQuestion("q"),),
        minimum_independent_sources=2,
    )
    a = EvidenceItem(
        source="web",
        canonical_url="https://docs.vendor.example/a",
        claim="fact",
        metadata={"publisher_id": "Vendor"},
    )
    b = EvidenceItem(
        source="exa",
        canonical_url="https://news.vendor.example/b",
        claim="fact",
        metadata={"publisher_id": "vendor"},
    )
    result = evaluate_policy(plan, EvidenceStore([a, b]))
    assert result.independent_sources == 1
    assert result.satisfied is False


def test_www_prefix_does_not_create_fake_independence():
    plan = ResearchPlan(
        topic="x",
        questions=(ResearchQuestion("q"),),
        minimum_independent_sources=2,
    )
    a = EvidenceItem(
        source="web",
        canonical_url="https://www.example.test/a",
        claim="fact",
    )
    b = EvidenceItem(
        source="exa",
        canonical_url="https://example.test/b",
        claim="fact",
    )
    result = evaluate_policy(plan, EvidenceStore([a, b]))
    assert result.independent_sources == 1


def test_publisher_aliases_do_not_inflate_independence():
    plan = ResearchPlan(
        topic="x",
        questions=(ResearchQuestion("q"),),
        minimum_independent_sources=2,
    )
    store = EvidenceStore(
        [
            EvidenceItem(
                source="web",
                canonical_url="https://www.reddit.com/r/test/comments/1",
                claim="a",
            ),
            EvidenceItem(
                source="exa",
                canonical_url="https://reddit.com/r/test/comments/2",
                claim="b",
            ),
        ]
    )
    result = evaluate_policy(plan, store)
    assert result.independent_sources == 1
    assert result.satisfied is False
