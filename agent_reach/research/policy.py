"""Research coverage policy evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from urllib.parse import urlsplit

from .models import EvidenceItem, SourceKind
from .planner import ResearchPlan
from .store import EvidenceStore


@dataclass(frozen=True)
class PolicyResult:
    satisfied: bool
    independent_sources: int
    primary_sources: int
    reasons: tuple[str, ...]


def source_identity(item: EvidenceItem) -> str:
    """Best available identity for conservative independence counting."""
    if item.canonical_url:
        try:
            host = (urlsplit(item.canonical_url).hostname or "").lower().rstrip(".")
        except ValueError:
            host = ""
        if host:
            return "host:" + host
    return "channel:" + item.source


def _items_for_ids(store: EvidenceStore, ids: Set[str]) -> list[EvidenceItem]:
    return [
        item
        for evidence_id in ids
        if (item := store.get(evidence_id)) is not None
    ]


def evaluate_policy(
    plan: ResearchPlan,
    store: EvidenceStore,
    question_evidence: Mapping[str, Set[str]] | None = None,
) -> PolicyResult:
    identities = {source_identity(item) for item in store.all()}
    primary_identities = {
        source_identity(item)
        for item in store.all()
        if item.source_kind == SourceKind.PRIMARY
    }
    reasons: list[str] = []

    if question_evidence is None:
        if len(identities) < plan.minimum_independent_sources:
            reasons.append(
                f"need {plan.minimum_independent_sources} independent sources; "
                f"have {len(identities)}"
            )
    else:
        for question in plan.questions:
            items = _items_for_ids(
                store,
                question_evidence.get(question.text, set()),
            )
            question_identities = {source_identity(item) for item in items}
            if len(question_identities) < plan.minimum_independent_sources:
                reasons.append(
                    f"question {question.text!r} needs "
                    f"{plan.minimum_independent_sources} independent sources; "
                    f"have {len(question_identities)}"
                )

    required_primary_questions = [
        question for question in plan.questions if question.require_primary_source
    ]
    if question_evidence is None:
        if required_primary_questions and not primary_identities:
            reasons.append("plan requires primary-source evidence but none was collected")
    else:
        for question in required_primary_questions:
            items = _items_for_ids(
                store,
                question_evidence.get(question.text, set()),
            )
            if not any(item.source_kind == SourceKind.PRIMARY for item in items):
                reasons.append(
                    f"question {question.text!r} requires primary-source evidence"
                )

    return PolicyResult(
        satisfied=not reasons,
        independent_sources=len(identities),
        primary_sources=len(primary_identities),
        reasons=tuple(reasons),
    )
