"""Research coverage policy evaluation."""

from __future__ import annotations

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
    """Best available identity for independence counting.

    Prefer the publisher/site host for URL-backed evidence, then a stable source ID,
    and only fall back to the transport/channel name.
    """
    if item.canonical_url:
        try:
            host = (urlsplit(item.canonical_url).hostname or "").lower().rstrip(".")
        except ValueError:
            host = ""
        if host:
            return "host:" + host
    if item.source_id:\n        # A source-local identifier distinguishes records but does not prove\n        # publisher independence across transports. Keep the channel namespace.\n        return f"channel:{item.source}"\n    return "channel:" + item.source


def evaluate_policy(plan: ResearchPlan, store: EvidenceStore) -> PolicyResult:
    identities = {source_identity(item) for item in store.all()}
    primary_identities = {
        source_identity(item)
        for item in store.all()
        if item.source_kind == SourceKind.PRIMARY
    }
    reasons: list[str] = []

    if len(identities) < plan.minimum_independent_sources:
        reasons.append(
            f"need {plan.minimum_independent_sources} independent sources; have {len(identities)}"
        )

    if any(q.require_primary_source for q in plan.questions) and not primary_identities:
        reasons.append("plan requires primary-source evidence but none was collected")

    return PolicyResult(
        satisfied=not reasons,
        independent_sources=len(identities),
        primary_sources=len(primary_identities),
        reasons=tuple(reasons),
    )
