"""Claim-level corroboration helpers."""

from __future__ import annotations

import re
from dataclasses import replace

from .models import EvidenceItem
from .policy import source_identity
from .store import EvidenceStore

_WS = re.compile(r"\s+")


def claim_key(text: str) -> str:
    return _WS.sub(" ", text).strip().casefold()


def link_exact_claims(store: EvidenceStore) -> EvidenceStore:
    """Link identical normalized claims across independent source identities."""
    groups: dict[str, list[EvidenceItem]] = {}
    for item in store.all():
        groups.setdefault(claim_key(item.claim), []).append(item)

    linked = EvidenceStore()
    for items in groups.values():
        for item in items:
            corroborates = tuple(
                other.evidence_id
                for other in items
                if other.evidence_id != item.evidence_id
                and source_identity(other) != source_identity(item)
            )
            linked.add(replace(item, corroborates=corroborates))
    return linked
