from agent_reach.research.models import EvidenceItem, SourceKind
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.report import render_markdown
from agent_reach.research.runner import ResearchRun


def test_report_surfaces_unsatisfied_policy():
    plan = ResearchPlan(
        topic="GPU",
        questions=(ResearchQuestion("memory?", require_primary_source=True),),
        minimum_independent_sources=2,
    )
    run = ResearchRun(plan)
    run.store.add(EvidenceItem(source="reddit", source_id="1", claim="32 GB", source_kind=SourceKind.COMMUNITY))
    text = render_markdown(run)
    assert "Satisfied: false" in text
    assert "need 2 independent sources; have 1" in text
    assert "requires primary-source evidence" in text
