"""Research coverage policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .models import SourceKind
from .planner import ResearchPlan
from .store import EvidenceStore


@dataclass(frozen=True)
class PolicyResult:
    satisfied: bool
    independent_sources: int
    primary_sources: int
    reasons: tuple[str, ...]


def evaluate_policy(plan: ResearchPlan, store: EvidenceStore) -> PolicyResult:
    sources = {item.source for item in store.all()}
    primary_sources = {
        item.source for item in store.all() if item.source_kind == SourceKind.PRIMARY
    }
    reasons: list[str] = []

    if len(sources) < plan.minimum_independent_sources:
        reasons.append(
            f"need {plan.minimum_independent_sources} independent sources; have {len(sources)}"
        )

    if any(q.require_primary_source for q in plan.questions) and not primary_sources:
        reasons.append("plan requires primary-source evidence but none was collected")

    return PolicyResult(
        satisfied=not reasons,
        independent_sources=len(sources),
        primary_sources=len(primary_sources),
        reasons=tuple(reasons),
    )
