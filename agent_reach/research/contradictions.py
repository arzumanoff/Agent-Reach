"""Deterministic contradiction links supplied by explicit claim relations."""

from __future__ import annotations

from dataclasses import replace

from .store import EvidenceStore


def link_contradictions(
    store: EvidenceStore,
    pairs: list[tuple[str, str]],
) -> EvidenceStore:
    """Return a copy with symmetric contradiction links.

    Pairs contain evidence IDs. Claim interpretation remains outside the deterministic
    core; once a reviewer/model marks a pair contradictory, storage and reporting are
    reproducible.
    """
    mapping = {item.evidence_id: item for item in store.all()}
    links: dict[str, set[str]] = {evidence_id: set() for evidence_id in mapping}
    for left, right in pairs:
        if left == right or left not in mapping or right not in mapping:
            continue
        links[left].add(right)
        links[right].add(left)

    out = EvidenceStore()
    for evidence_id, item in mapping.items():
        merged = tuple(sorted(set(item.contradicts).union(links[evidence_id])))
        out.add(replace(item, contradicts=merged))
    return out
