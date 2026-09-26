"""Deterministic summaries for collected research evidence."""

from __future__ import annotations

from .models import EvidenceState
from .store import EvidenceStore
from .verification import derive_state


def build_summary(store: EvidenceStore) -> dict[str, int]:
    counts = {state.value: 0 for state in EvidenceState}
    for item in store.all():
        counts[derive_state(item, store).value] += 1
    counts["total"] = len(store)
    return counts
