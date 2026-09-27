import json

import pytest

from agent_reach.research.artifacts import ArtifactKind, ArtifactRef
from agent_reach.research.cli import run_document
from agent_reach.research.models import EvidenceItem, SourceKind
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.runner import ResearchRun
from agent_reach.research.serialization import deserialize_run, serialize_run


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


def test_artifact_survives_serialization_round_trip():

    run = ResearchRun(ResearchPlan(topic="x", questions=(ResearchQuestion("q"),)))
    item = EvidenceItem(
        source="google_images",
        canonical_url="https://vendor.example/page",
        claim="PCB image",
        artifact_refs=(
            ArtifactRef(
                ArtifactKind.IMAGE,
                "https://img.example/pcb.jpg",
                "google_images",
            ),
        ),
    )
    run.store.add(item)
    payload = json.loads(json.dumps(serialize_run(run)))
    restored = deserialize_run(payload)
    artifact = restored.store.all()[0].artifact_refs[0]
    assert artifact.kind == ArtifactKind.IMAGE
    assert artifact.locator == "https://img.example/pcb.jpg"


def test_deserialize_rejects_unknown_question_evidence_id():
    payload = {
        "schema_version": 1,
        "plan": {
            "topic": "x",
            "questions": [{"text": "q", "preferred_sources": []}],
            "max_results_per_source": 10,
            "minimum_independent_sources": 1,
            "notes": [],
        },
        "coverage_gaps": [],
        "attempted_queries": 0,
        "successful_queries": 0,
        "discarded_results": 0,
        "question_evidence": {"q": ["missing"]},
        "evidence": [],
    }
    with pytest.raises(ValueError, match="unknown evidence"):
        deserialize_run(payload)


def test_deserialize_rejects_impossible_query_metrics():
    payload = {
        "schema_version": 1,
        "plan": {
            "topic": "x",
            "questions": [{"text": "q", "preferred_sources": []}],
            "max_results_per_source": 10,
            "minimum_independent_sources": 1,
            "notes": [],
        },
        "coverage_gaps": [],
        "attempted_queries": 1,
        "successful_queries": 2,
        "discarded_results": 0,
        "question_evidence": {},
        "evidence": [],
    }
    with pytest.raises(ValueError, match="cannot exceed"):
        deserialize_run(payload)


def test_deserialize_rejects_unknown_artifact_kind():
    payload = {
        "schema_version": 1,
        "plan": {
            "topic": "x",
            "questions": [{"text": "q", "preferred_sources": []}],
            "max_results_per_source": 10,
            "minimum_independent_sources": 1,
            "notes": [],
        },
        "coverage_gaps": [],
        "attempted_queries": 0,
        "successful_queries": 0,
        "discarded_results": 0,
        "question_evidence": {},
        "evidence": [{
            "source": "web",
            "claim": "claim",
            "source_kind": "secondary",
            "state": "single-source",
            "artifact_refs": [{
                "kind": "mystery",
                "locator": "https://example.test/a",
                "source": "web",
            }],
            "corroborates": [],
            "contradicts": [],
            "metadata": {},
        }],
    }
    with pytest.raises(ValueError, match="invalid kind"):
        deserialize_run(payload)


def test_artifact_round_trip_is_json_safe():

    run = ResearchRun(
        ResearchPlan(
            topic="image",
            questions=(ResearchQuestion("pcb", ("google_images",)),),
            minimum_independent_sources=1,
        )
    )
    item = EvidenceItem(
        source="google_images",
        canonical_url="https://vendor.example/board",
        claim="PCB photo",
        artifact_refs=(
            ArtifactRef(
                kind=ArtifactKind.IMAGE,
                locator="https://images.example/pcb.jpg",
                source="google_images",
                description="PCB",
            ),
        ),
    )
    evidence_id = run.store.add(item)
    run.question_evidence["pcb"] = {evidence_id}

    payload = json.loads(json.dumps(serialize_run(run)))
    replayed = deserialize_run(payload)
    artifact = replayed.store.all()[0].artifact_refs[0]

    assert artifact.kind == ArtifactKind.IMAGE
    assert artifact.locator == "https://images.example/pcb.jpg"


def test_deserialize_rejects_tampered_evidence_id():
    run = ResearchRun(
        ResearchPlan(topic="x", questions=(ResearchQuestion("q"),))
    )
    run.store.add(EvidenceItem(source="web", source_id="1", claim="fact"))
    payload = json.loads(json.dumps(serialize_run(run)))
    payload["evidence"][0]["evidence_id"] = "tampered"

    with pytest.raises(ValueError, match="evidence_id"):
        deserialize_run(payload)
