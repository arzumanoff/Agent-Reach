from agent_reach.research.models import EvidenceItem
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.report import render_markdown
from agent_reach.research.runner import ResearchRun


def test_markdown_report_preserves_locator_and_gaps():
    plan = ResearchPlan(topic="GPU", questions=(ResearchQuestion("memory?"),))
    run = ResearchRun(plan)
    run.store.add(EvidenceItem(source="github", source_id="issue:1", claim="32 GB", title="Issue"))
    run.coverage_gaps.append("arxiv: no results")
    text = render_markdown(run)
    assert "# Research report: GPU" in text
    assert "Locator: issue:1" in text
    assert "arxiv: no results" in text
