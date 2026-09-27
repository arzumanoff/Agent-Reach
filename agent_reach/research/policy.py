"""Research coverage policy evaluation."""

from __future__ import annotations

from collections.abc import Mapping, Set
from dataclasses import dataclass
from urllib.parse import urlsplit

from .models import EvidenceItem, SourceKind
from .planner import ResearchPlan
from .store import EvidenceStore

_PUBLISHER_HOST_ALIASES = {
    "export.arxiv.org": "arxiv.org",
    "api.github.com": "github.com",
    "www.github.com": "github.com",
    "www.reddit.com": "reddit.com",
    "old.reddit.com": "reddit.com",
    "www.youtube.com": "youtube.com",
    "m.youtube.com": "youtube.com",
}


@dataclass(frozen=True)
class PolicyResult:
    satisfied: bool
    independent_sources: int
    primary_sources: int
    reasons: tuple[str, ...]


def _publisher_host(host: str) -> str:
    normalized = host.lower().rstrip(".")
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return _PUBLISHER_HOST_ALIASES.get(normalized, normalized)


def source_identity(item: EvidenceItem) -> str:
    """Best available identity for conservative independence counting."""
    publisher_id = item.metadata.get("publisher_id")
    if isinstance(publisher_id, str) and publisher_id.strip():
        return "publisher:" + publisher_id.strip().casefold()

    if item.canonical_url:
        try:
            host = (urlsplit(item.canonical_url).hostname or "").lower().rstrip(".")
        except ValueError:
            host = ""
        if host:
            return "host:" + _publisher_host(host)

    return "channel:" + item.source


def _identities_for_ids(
    store: EvidenceStore,
    evidence_ids: Set[str],
) -> set[str]:
    identities: set[str] = set()
    for evidence_id in evidence_ids:
        item = store.get(evidence_id)
        if item is not None:
            identities.add(source_identity(item))
    return identities


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
            ids = question_evidence.get(question.text, set())
            question_identities = _identities_for_ids(store, ids)
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
        if not primary_identities:
            for question in required_primary_questions:
                reasons.append(
                    f"question {question.text!r} requires primary-source evidence"
                )
    else:
        for question in required_primary_questions:
            ids = question_evidence.get(question.text, set())
            has_primary = any(
                (item := store.get(evidence_id)) is not None
                and item.source_kind == SourceKind.PRIMARY
                for evidence_id in ids
            )
            if not has_primary:
                reasons.append(
                    f"question {question.text!r} requires primary-source evidence"
                )

    return PolicyResult(
        satisfied=not reasons,
        independent_sources=len(identities),
        primary_sources=len(primary_identities),
        reasons=tuple(reasons),
    )
