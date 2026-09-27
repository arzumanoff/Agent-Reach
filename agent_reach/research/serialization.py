"""Serialization for replayable research runs."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import EvidenceItem, EvidenceState, SourceKind
from .planner import ResearchPlan, ResearchQuestion
from .runner import ResearchRun
from .store import EvidenceStore
from .verification import derive_state


def serialize_run(run: ResearchRun) -> dict[str, Any]:
    evidence = []
    for item in run.store.all():
        payload = asdict(item)
        payload["source_kind"] = item.source_kind.value
        payload["state"] = derive_state(item, run.store).value
        payload["evidence_id"] = item.evidence_id
        evidence.append(payload)

    return {
        "schema_version": 1,
        "plan": asdict(run.plan),
        "coverage_gaps": list(run.coverage_gaps),
        "attempted_queries": run.attempted_queries,
        "successful_queries": run.successful_queries,
        "discarded_results": run.discarded_results,
        "question_evidence": {
            question: sorted(ids)
            for question, ids in sorted(run.question_evidence.items())
        },
        "evidence": evidence,
    }


def deserialize_run(payload: dict[str, Any]) -> ResearchRun:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported research schema version")

    raw_plan = payload.get("plan")
    if not isinstance(raw_plan, dict):
        raise ValueError("serialized research run is missing plan")

    raw_questions = raw_plan.get("questions")
    if not isinstance(raw_questions, list):
        raise ValueError("serialized research plan has invalid questions")

    questions = tuple(
        ResearchQuestion(
            text=str(question["text"]),
            preferred_sources=tuple(question.get("preferred_sources", ())),
            require_primary_source=bool(question.get("require_primary_source", False)),
        )
        for question in raw_questions
        if isinstance(question, dict)
    )
    plan = ResearchPlan(
        topic=str(raw_plan.get("topic", "")),
        questions=questions,
        max_results_per_source=int(raw_plan.get("max_results_per_source", 10)),
        minimum_independent_sources=int(
            raw_plan.get("minimum_independent_sources", 2)
        ),
        notes=tuple(raw_plan.get("notes", ())),
    )

    items: list[EvidenceItem] = []
    raw_evidence = payload.get("evidence", [])
    if not isinstance(raw_evidence, list):
        raise ValueError("serialized research evidence must be a list")

    for raw in raw_evidence:
        if not isinstance(raw, dict):
            continue
        items.append(
            EvidenceItem(
                source=str(raw.get("source", "")),
                claim=str(raw.get("claim", "")),
                canonical_url=raw.get("canonical_url"),
                source_id=raw.get("source_id"),
                title=raw.get("title"),
                author=raw.get("author"),
                published_at=raw.get("published_at"),
                source_kind=SourceKind(raw.get("source_kind", "unknown")),
                state=EvidenceState(raw.get("state", "unverified")),
                artifact_refs=tuple(raw.get("artifact_refs", ())),
                corroborates=tuple(raw.get("corroborates", ())),
                contradicts=tuple(raw.get("contradicts", ())),
                backend=raw.get("backend"),
                retrieved_at=str(raw.get("retrieved_at", "")),
                metadata=dict(raw.get("metadata", {})),
            )
        )

    run = ResearchRun(
        plan=plan,
        store=EvidenceStore(items),
        coverage_gaps=list(payload.get("coverage_gaps", ())),
        attempted_queries=int(payload.get("attempted_queries", 0)),
        successful_queries=int(payload.get("successful_queries", 0)),
        discarded_results=int(payload.get("discarded_results", 0)),
    )

    raw_question_evidence = payload.get("question_evidence", {})
    if isinstance(raw_question_evidence, dict):
        run.question_evidence = {
            str(question): {str(evidence_id) for evidence_id in ids}
            for question, ids in raw_question_evidence.items()
            if isinstance(ids, list)
        }

    return run
