"""Boundary for optional semantic claim comparison.

The deterministic core never calls a model by itself. A caller may supply a comparator
that returns only a relation label; evidence links remain explicit and replayable.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from .models import EvidenceItem


class ClaimRelation(str, Enum):
    SAME = "same"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    UNRELATED = "unrelated"
    UNCERTAIN = "uncertain"


SemanticComparator = Callable[[EvidenceItem, EvidenceItem], ClaimRelation]


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
