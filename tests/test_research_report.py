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


def test_report_includes_discarded_result_count():
    plan = ResearchPlan(topic="GPU", questions=(ResearchQuestion("memory?"),))
    run = ResearchRun(plan)
    run.discarded_results = 3
    assert "Results discarded: 3" in render_markdown(run)


def test_report_renders_question_coverage_and_graph_links():
    plan = ResearchPlan(topic="GPU", questions=(ResearchQuestion("memory?"),))
    run = ResearchRun(plan)
    a = EvidenceItem(source="official", canonical_url="https://vendor.example/spec", claim="32 GB")
    b = EvidenceItem(
        source="lab",
        canonical_url="https://lab.example/test",
        claim="32 GB",
        corroborates=(a.evidence_id,),
    )
    run.store.add(a)
    run.store.add(b)
    run.question_evidence["memory?"] = {a.evidence_id, b.evidence_id}
    text = render_markdown(run)
    assert "## Question coverage" in text
    assert "Evidence items: 2" in text
    assert "Independent source identities: 2" in text
    assert "Corroborates:" in text
