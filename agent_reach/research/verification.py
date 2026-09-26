"""Deterministic evidence-state derivation.

This module intentionally does not ask an LLM to invent a probability. It derives
an evidence state from explicit corroboration/contradiction links and source diversity.
"""

from __future__ import annotations

from dataclasses import replace

from .models import EvidenceItem, EvidenceState
from .store import EvidenceStore


def derive_state(item: EvidenceItem, store: EvidenceStore) -> EvidenceState:
    if item.contradicts:
        return EvidenceState.CONTRADICTED

    corroborating_sources = {
        linked.source
        for evidence_id in item.corroborates
        if (linked := store.get(evidence_id)) is not None
        and linked.source != item.source
    }
    if len(corroborating_sources) >= 2:
        return EvidenceState.CONFIRMED
    if corroborating_sources:
        return EvidenceState.CORROBORATED

    if item.canonical_url or item.source_id:
        return EvidenceState.SINGLE_SOURCE
    return EvidenceState.UNVERIFIED


def with_derived_state(item: EvidenceItem, store: EvidenceStore) -> EvidenceItem:
    return replace(item, state=derive_state(item, store))
