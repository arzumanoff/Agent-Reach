"""Normalize channel results into provenance-preserving evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import EvidenceItem, SourceKind


def evidence_from_result(
    source: str,
    result: Mapping[str, Any],
    *,
    claim: str | None = None,
    backend: str | None = None,
    source_kind: SourceKind = SourceKind.UNKNOWN,
) -> EvidenceItem:
    canonical_url = _first(result, "url", "link", "hn_url")
    source_id = _first(result, "id", "arxiv_id", "objectID")
    title = _first(result, "title")
    author = _author(result)
    published = _first(result, "published", "created_at", "time")
    text = claim or _first(result, "summary", "snippet", "text", "title") or ""

    return EvidenceItem(
        source=source,
        claim=str(text),
        canonical_url=str(canonical_url) if canonical_url else None,
        source_id=str(source_id) if source_id else None,
        title=str(title) if title else None,
        author=author,
        published_at=str(published) if published else None,
        source_kind=source_kind,
        backend=backend,
        metadata={"raw_keys": tuple(sorted(str(k) for k in result))},
    )


def _first(result: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = result.get(key)
        if value not in (None, "", [], ()):
            return value
    return None


def _author(result: Mapping[str, Any]) -> str | None:
    value = result.get("author")
    if value:
        return str(value)
    authors = result.get("authors")
    if isinstance(authors, (list, tuple)) and authors:
        return ", ".join(str(x) for x in authors)
    return None
