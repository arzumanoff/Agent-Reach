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
