import pytest

from agent_reach.research.planner import ResearchPlan, ResearchQuestion


def test_plan_requires_questions():
    with pytest.raises(ValueError):
        ResearchPlan(topic="GPU research", questions=())


def test_requested_sources_preserve_order_and_deduplicate():
    plan = ResearchPlan(
        topic="GPU research",
        questions=(
            ResearchQuestion("Find hardware evidence", ("github", "youtube")),
            ResearchQuestion("Find independent discussion", ("reddit", "github")),
        ),
    )
    assert plan.requested_sources == ("github", "youtube", "reddit")
