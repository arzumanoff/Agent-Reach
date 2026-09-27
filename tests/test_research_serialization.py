import json

from agent_reach.research.models import EvidenceItem
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.runner import ResearchRun
from agent_reach.research.serialization import serialize_run


def test_serialized_run_has_schema_and_stable_evidence_id():
    run = ResearchRun(ResearchPlan(topic="x", questions=(ResearchQuestion("q"),)))
    item = EvidenceItem(source="github", source_id="1", claim="claim")
    run.store.add(item)
    run.discarded_results = 2
    payload = serialize_run(run)
    assert payload["schema_version"] == 1
    assert payload["evidence"][0]["evidence_id"] == item.evidence_id
    assert payload["evidence"][0]["state"] == "single-source"
    assert payload["discarded_results"] == 2
    json.dumps(payload)


def test_serialized_run_round_trips_through_cli():
    import json

    from agent_reach.research.cli import run_document
    from agent_reach.research.models import SourceKind

    plan = ResearchPlan(
        topic="GPU",
        questions=(
            ResearchQuestion(
                "memory?",
                ("arxiv",),
                require_primary_source=True,
            ),
        ),
        minimum_independent_sources=1,
    )
    run = ResearchRun(plan)
    item = EvidenceItem(
        source="arxiv",
        canonical_url="https://arxiv.org/abs/2601.1",
        source_id="2601.1",
        claim="32 GB",
        source_kind=SourceKind.PRIMARY,
    )
    evidence_id = run.store.add(item)
    run.question_evidence["memory?"] = {evidence_id}
    run.attempted_queries = 1
    run.successful_queries = 1

    payload = json.loads(json.dumps(serialize_run(run)))
    report = run_document(payload)

    assert "Research report: GPU" in report
    assert "32 GB" in report
    assert "Satisfied: true" in report
    assert "Queries attempted: 1" in report
