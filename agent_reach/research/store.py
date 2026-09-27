"""In-memory evidence collection with deterministic deduplication."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace

from .artifacts import ArtifactRef
from .models import EvidenceItem, SourceKind

_SOURCE_KIND_RANK = {
    SourceKind.UNKNOWN: 0,
    SourceKind.COMMUNITY: 1,
    SourceKind.SECONDARY: 2,
    SourceKind.PRIMARY: 3,
}


def _merge_artifacts(
    left: tuple[ArtifactRef, ...],
    right: tuple[ArtifactRef, ...],
) -> tuple[ArtifactRef, ...]:
    values = {artifact for artifact in (*left, *right)}
    return tuple(
        sorted(
            values,
            key=lambda artifact: (
                artifact.kind.value,
                artifact.locator,
                artifact.source,
                artifact.description or "",
                artifact.content_hash or "",
            ),
        )
    )


def _merge_items(left: EvidenceItem, right: EvidenceItem) -> EvidenceItem:
    if left.evidence_id != right.evidence_id:
        raise ValueError("cannot merge different evidence IDs")

    strongest_kind = max(
        (left.source_kind, right.source_kind),
        key=lambda kind: _SOURCE_KIND_RANK[kind],
    )
    seen_sources = sorted({left.source, right.source})
    metadata = dict(left.metadata)
    for key, value in right.metadata.items():
        metadata.setdefault(key, value)
    prior_seen = set()
    for candidate in (left.metadata.get("seen_sources"), right.metadata.get("seen_sources")):
        if isinstance(candidate, list):
            prior_seen.update(str(value) for value in candidate)
    all_seen = sorted(prior_seen.union(seen_sources))
    if len(all_seen) > 1:
        metadata["seen_sources"] = all_seen
    else:
        metadata.pop("seen_sources", None)

    return replace(
        left,
        source=min(left.source, right.source),
        title=left.title or right.title,
        author=left.author or right.author,
        published_at=left.published_at or right.published_at,
        source_kind=strongest_kind,
        artifact_refs=_merge_artifacts(left.artifact_refs, right.artifact_refs),
        corroborates=tuple(sorted(set(left.corroborates).union(right.corroborates))),
        contradicts=tuple(sorted(set(left.contradicts).union(right.contradicts))),
        backend=left.backend or right.backend,
        retrieved_at=min(left.retrieved_at, right.retrieved_at),
        metadata=metadata,
    )


class EvidenceStore:
    def __init__(self, items: Iterable[EvidenceItem] = ()) -> None:
        self._items: dict[str, EvidenceItem] = {}
        for item in items:
            self.add(item)

    def add(self, item: EvidenceItem) -> str:
        """Add or deterministically merge evidence and return its stable ID."""
        evidence_id = item.evidence_id
        existing = self._items.get(evidence_id)
        self._items[evidence_id] = (
            item if existing is None else _merge_items(existing, item)
        )
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
