"""Serialization for replayable research runs."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .artifacts import ArtifactKind, ArtifactRef
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
        payload["artifact_refs"] = [
            {
                "kind": artifact.kind.value,
                "locator": artifact.locator,
                "source": artifact.source,
                "description": artifact.description,
                "content_hash": artifact.content_hash,
            }
            for artifact in item.artifact_refs
        ]
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


def _nonnegative_int(payload: dict[str, Any], key: str) -> int:
    try:
        value = int(payload.get(key, 0))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"serialized research field {key!r} must be an integer") from exc
    if value < 0:
        raise ValueError(f"serialized research field {key!r} must be non-negative")
    return value


def _string_tuple(raw: Any, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        raise ValueError(f"{label} must be a list")
    return tuple(str(value) for value in raw)


def _artifact_from_payload(raw: Any) -> ArtifactRef:
    if not isinstance(raw, dict):
        raise ValueError("serialized artifact must be an object")
    try:
        kind = ArtifactKind(raw.get("kind"))
    except (TypeError, ValueError) as exc:
        raise ValueError("serialized artifact has invalid kind") from exc
    return ArtifactRef(
        kind=kind,
        locator=str(raw.get("locator", "")),
        source=str(raw.get("source", "")),
        description=raw.get("description"),
        content_hash=raw.get("content_hash"),
    )


def deserialize_run(payload: dict[str, Any]) -> ResearchRun:
    if not isinstance(payload, dict):
        raise ValueError("serialized research run must be an object")
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported research schema version")

    raw_plan = payload.get("plan")
    if not isinstance(raw_plan, dict):
        raise ValueError("serialized research run is missing plan")

    raw_questions = raw_plan.get("questions")
    if not isinstance(raw_questions, list):
        raise ValueError("serialized research plan has invalid questions")

    questions: list[ResearchQuestion] = []
    for question in raw_questions:
        if not isinstance(question, dict) or "text" not in question:
            raise ValueError("serialized research question must be an object with text")
        questions.append(
            ResearchQuestion(
                text=str(question["text"]),
                preferred_sources=_string_tuple(
                    question.get("preferred_sources", ()),
                    "preferred_sources",
                ),
                require_primary_source=bool(
                    question.get("require_primary_source", False)
                ),
            )
        )

    plan = ResearchPlan(
        topic=str(raw_plan.get("topic", "")),
        questions=tuple(questions),
        max_results_per_source=int(raw_plan.get("max_results_per_source", 10)),
        minimum_independent_sources=int(
            raw_plan.get("minimum_independent_sources", 2)
        ),
        notes=_string_tuple(raw_plan.get("notes", ()), "plan notes"),
    )

    raw_evidence = payload.get("evidence", [])
    if not isinstance(raw_evidence, list):
        raise ValueError("serialized research evidence must be a list")

    items: list[EvidenceItem] = []
    for raw in raw_evidence:
        if not isinstance(raw, dict):
            raise ValueError("serialized evidence item must be an object")

        raw_metadata = raw.get("metadata", {})
        if not isinstance(raw_metadata, dict):
            raise ValueError("serialized evidence metadata must be an object")

        raw_artifacts = raw.get("artifact_refs", ())
        if not isinstance(raw_artifacts, (list, tuple)):
            raise ValueError("serialized artifact_refs must be a list")

        try:
            source_kind = SourceKind(raw.get("source_kind", "unknown"))
            state = EvidenceState(raw.get("state", "unverified"))
        except (TypeError, ValueError) as exc:
            raise ValueError("serialized evidence has invalid enum value") from exc

        item = EvidenceItem(
                source=str(raw.get("source", "")),
                claim=str(raw.get("claim", "")),
                canonical_url=raw.get("canonical_url"),
                source_id=raw.get("source_id"),
                title=raw.get("title"),
                author=raw.get("author"),
                published_at=raw.get("published_at"),
                source_kind=source_kind,
                state=state,
                artifact_refs=tuple(
                    _artifact_from_payload(artifact)
                    for artifact in raw_artifacts
                ),
                corroborates=_string_tuple(
                    raw.get("corroborates", ()),
                    "evidence corroborates",
                ),
                contradicts=_string_tuple(
                    raw.get("contradicts", ()),
                    "evidence contradicts",
                ),
                backend=raw.get("backend"),
                retrieved_at=str(raw.get("retrieved_at", "")),
                metadata=dict(raw_metadata),
            )
        serialized_id = raw.get("evidence_id")
        if serialized_id is not None and str(serialized_id) != item.evidence_id:
            raise ValueError("serialized evidence_id does not match evidence content")
        items.append(item)

    raw_gaps = payload.get("coverage_gaps", ())
    if not isinstance(raw_gaps, (list, tuple)):
        raise ValueError("serialized coverage_gaps must be a list")

    run = ResearchRun(
        plan=plan,
        store=EvidenceStore(items),
        coverage_gaps=[str(gap) for gap in raw_gaps],
        attempted_queries=_nonnegative_int(payload, "attempted_queries"),
        successful_queries=_nonnegative_int(payload, "successful_queries"),
        discarded_results=_nonnegative_int(payload, "discarded_results"),
    )

    if run.successful_queries > run.attempted_queries:
        raise ValueError("successful_queries cannot exceed attempted_queries")

    raw_question_evidence = payload.get("question_evidence", {})
    if not isinstance(raw_question_evidence, dict):
        raise ValueError("serialized question_evidence must be an object")

    known_ids = {item.evidence_id for item in run.store.all()}
    known_questions = {question.text for question in plan.questions}
    for question, ids in raw_question_evidence.items():
        if str(question) not in known_questions:
            raise ValueError("serialized question_evidence references unknown question")
        if not isinstance(ids, list):
            raise ValueError("serialized question evidence IDs must be a list")
        normalized_ids = {str(evidence_id) for evidence_id in ids}
        unknown_ids = normalized_ids - known_ids
        if unknown_ids:
            raise ValueError("serialized question_evidence references unknown evidence")
        run.question_evidence[str(question)] = normalized_ids

    return run
