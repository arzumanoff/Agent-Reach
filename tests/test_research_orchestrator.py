from agent_reach.research.models import SourceKind
from agent_reach.research.orchestrator import execute_research
from agent_reach.research.planner import ResearchPlan, ResearchQuestion


def test_execute_research_runs_end_to_end():
    plan = ResearchPlan(
        topic="memory",
        questions=(ResearchQuestion("32 GB?", ("official", "community"), require_primary_source=True),),
        minimum_independent_sources=2,
    )
    searches = {
        "official": lambda q, n: [{"id": "a", "title": "spec", "text": "32 GB"}],
        "community": lambda q, n: [{"id": "b", "title": "report", "text": "32 GB"}],
    }
    run, policy, report = execute_research(
        plan,
        searches,
        {"official": SourceKind.PRIMARY, "community": SourceKind.COMMUNITY},
    )
    assert len(run.store) == 2
    assert policy.satisfied is True
    assert "Satisfied: true" in report
