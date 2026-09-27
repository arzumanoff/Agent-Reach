"""Boundary for optional semantic claim comparison."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from enum import Enum

from .models import EvidenceItem
from .store import EvidenceStore


class ClaimRelation(str, Enum):
    SAME = "same"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    UNRELATED = "unrelated"
    UNCERTAIN = "uncertain"


SemanticComparator = Callable[[EvidenceItem, EvidenceItem], ClaimRelation]
RelationDecision = tuple[str, str, ClaimRelation]


def compare_pair(
    left: EvidenceItem,
    right: EvidenceItem,
    comparator: SemanticComparator,
) -> ClaimRelation:
    if left.evidence_id == right.evidence_id:
        return ClaimRelation.SAME
    relation = comparator(left, right)
    if not isinstance(relation, ClaimRelation):
        raise TypeError("semantic comparator must return ClaimRelation")
    return relation


def apply_relations(
    store: EvidenceStore,
    decisions: Iterable[RelationDecision],
) -> EvidenceStore:
    """Apply explicit semantic decisions to a copy of the evidence graph."""
    mapping = {item.evidence_id: item for item in store.all()}
    supports: dict[str, set[str]] = {evidence_id: set() for evidence_id in mapping}
    contradicts: dict[str, set[str]] = {evidence_id: set() for evidence_id in mapping}

    for left_id, right_id, relation in decisions:
        if left_id == right_id or left_id not in mapping or right_id not in mapping:
            continue
        if relation in (ClaimRelation.SAME, ClaimRelation.SUPPORTS):
            supports[left_id].add(right_id)
            supports[right_id].add(left_id)
        elif relation == ClaimRelation.CONTRADICTS:
            contradicts[left_id].add(right_id)
            contradicts[right_id].add(left_id)
        elif relation in (ClaimRelation.UNRELATED, ClaimRelation.UNCERTAIN):
            continue
        else:
            raise TypeError("unsupported ClaimRelation")

    out = EvidenceStore()
    for evidence_id, item in mapping.items():
        out.add(
            replace(
                item,
                corroborates=tuple(
                    sorted(set(item.corroborates).union(supports[evidence_id]))
                ),
                contradicts=tuple(
                    sorted(set(item.contradicts).union(contradicts[evidence_id]))
                ),
            )
        )
    return out
