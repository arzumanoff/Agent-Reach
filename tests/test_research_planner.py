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


def test_question_rejects_empty_text_and_sources():
    with pytest.raises(ValueError):
        ResearchQuestion("   ")
    with pytest.raises(ValueError):
        ResearchQuestion("q", ("github", " "))


def test_plan_rejects_duplicate_question_text():
    with pytest.raises(ValueError, match="unique"):
        ResearchPlan(
            topic="x",
            questions=(
                ResearchQuestion("same"),
                ResearchQuestion("same"),
            ),
        )


def test_plan_rejects_duplicate_question_texts():
    with pytest.raises(ValueError, match="unique"):
        ResearchPlan(
            topic="x",
            questions=(
                ResearchQuestion("Same question"),
                ResearchQuestion(" same QUESTION "),
            ),
        )
