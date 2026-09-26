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
