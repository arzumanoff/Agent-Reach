from agent_reach.research.models import SourceKind
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.runner import ResearchRun


def test_runner_collects_multiple_sources_and_records_missing_adapter():
    plan = ResearchPlan(
        topic="test",
        questions=(ResearchQuestion("query", ("arxiv", "hackernews", "missing")),),
        max_results_per_source=2,
    )
    run = ResearchRun(plan)
    store = run.collect(
        {
            "arxiv": lambda q, n: [{"arxiv_id": "1", "title": "Paper", "summary": "claim"}],
            "hackernews": lambda q, n: [{"id": 2, "title": "Thread", "snippet": "discussion"}],
        },
        {"arxiv": SourceKind.PRIMARY, "hackernews": SourceKind.COMMUNITY},
    )
    assert len(store) == 2
    assert "query :: missing: no search adapter" in run.coverage_gaps


def test_runner_turns_source_failure_into_coverage_gap():
    def broken(query, limit):
        raise TimeoutError("late")

    plan = ResearchPlan(topic="test", questions=(ResearchQuestion("query", ("web",)),))
    run = ResearchRun(plan)
    assert len(run.collect({"web": broken})) == 0
    assert run.coverage_gaps == ["query :: web: TimeoutError"]


def test_runner_tracks_attempted_and_successful_queries():
    plan = ResearchPlan(topic="test", questions=(ResearchQuestion("query", ("ok", "empty")),))
    run = ResearchRun(plan)
    run.collect({
        "ok": lambda q, n: [{"id": "1", "title": "x", "text": "claim"}],
        "empty": lambda q, n: [],
    })
    assert run.attempted_queries == 2
    assert run.successful_queries == 1


def test_runner_discards_malformed_results_without_crashing():
    plan = ResearchPlan(topic="test", questions=(ResearchQuestion("query", ("web",)),))
    run = ResearchRun(plan)
    store = run.collect({"web": lambda q, n: [None, {"title": "", "text": ""}]})
    assert len(store) == 0
    assert run.discarded_results == 2
    assert any("no usable results" in gap for gap in run.coverage_gaps)
