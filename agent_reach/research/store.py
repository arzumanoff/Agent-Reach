"""In-memory evidence collection with deterministic deduplication."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import EvidenceItem


class EvidenceStore:
    def __init__(self, items: Iterable[EvidenceItem] = ()) -> None:
        self._items: dict[str, EvidenceItem] = {}
        for item in items:
            self.add(item)

    def add(self, item: EvidenceItem) -> str:
        """Add evidence once and return its deterministic ID."""
        evidence_id = item.evidence_id
        self._items.setdefault(evidence_id, item)
        return evidence_id

    def get(self, evidence_id: str) -> EvidenceItem | None:
        return self._items.get(evidence_id)

    def all(self) -> list[EvidenceItem]:
        """Return evidence in deterministic ID order."""
        return [self._items[key] for key in sorted(self._items)]

    def by_source(self) -> dict[str, list[EvidenceItem]]:
        grouped: dict[str, list[EvidenceItem]] = defaultdict(list)
        for item in self.all():
            grouped[item.source].append(item)
        return dict(sorted(grouped.items()))

    def __len__(self) -> int:
        return len(self._items)
