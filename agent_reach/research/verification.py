"""Deterministic evidence-state derivation."""

from __future__ import annotations

from dataclasses import replace

from .models import EvidenceItem, EvidenceState, SourceKind
from .policy import source_identity
from .store import EvidenceStore


def derive_state(item: EvidenceItem, store: EvidenceStore) -> EvidenceState:
    if item.contradicts:
        return EvidenceState.CONTRADICTED

    linked_items = [
        linked
        for evidence_id in item.corroborates
        if (linked := store.get(evidence_id)) is not None
        and source_identity(linked) != source_identity(item)
    ]
    corroborating_sources = {source_identity(linked) for linked in linked_items}

    # "Confirmed" is intentionally conservative: diversity alone is not enough.
    # At least one item in the evidence cluster must be primary evidence.
    has_primary = item.source_kind == SourceKind.PRIMARY or any(
        linked.source_kind == SourceKind.PRIMARY for linked in linked_items
    )
    if len(corroborating_sources) >= 2 and has_primary:
        return EvidenceState.CONFIRMED
    if corroborating_sources:
        return EvidenceState.CORROBORATED

    if item.canonical_url or item.source_id:
        return EvidenceState.SINGLE_SOURCE
    return EvidenceState.UNVERIFIED


def with_derived_state(item: EvidenceItem, store: EvidenceStore) -> EvidenceItem:
    return replace(item, state=derive_state(item, store))
