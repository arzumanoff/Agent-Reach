"""Normalize channel results into provenance-preserving evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from agent_reach.utils.text import scrub_url_credentials

from .artifacts import ArtifactKind, ArtifactRef
from .models import EvidenceItem, SourceKind


def _safe_url(value: object) -> str:
    """Remove userinfo and redact sensitive query values from a URL-like value."""
    text = str(value)
    try:
        parsed = urlsplit(text)
        _ = parsed.port
    except ValueError:
        return scrub_url_credentials(text)

    if not parsed.scheme or not parsed.hostname:
        return scrub_url_credentials(text)

    host = parsed.hostname
    port = parsed.port
    default_port = (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    )
    netloc = host if port is None or default_port else f"{host}:{port}"
    clean = urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )
    return scrub_url_credentials(clean)


def evidence_from_result(
    source: str,
    result: Mapping[str, Any],
    *,
    claim: str | None = None,
    backend: str | None = None,
    source_kind: SourceKind = SourceKind.UNKNOWN,
) -> EvidenceItem:
    metadata: dict[str, Any] = {
        "raw_keys": tuple(sorted(str(k) for k in result)),
    }
    artifacts: list[ArtifactRef] = []

    if source == "google_images":
        canonical_url = _first(result, "context_url", "url")
        artifact_url = result.get("url")
        if artifact_url:
            clean_artifact_url = _safe_url(artifact_url)
            metadata["artifact_url"] = clean_artifact_url
            artifacts.append(
                ArtifactRef(
                    kind=ArtifactKind.IMAGE,
                    locator=clean_artifact_url,
                    source=source,
                    description=str(result.get("title") or "") or None,
                )
            )
    elif source == "hackernews":
        canonical_url = _first(result, "hn_url", "url")
        if result.get("url"):
            metadata["external_url"] = _safe_url(result["url"])
    else:
        canonical_url = _first(result, "url", "link", "context_url")

    if canonical_url:
        canonical_url = _safe_url(canonical_url)

    if source == "google_images" and canonical_url and not artifacts:
        artifacts.append(
            ArtifactRef(
                kind=ArtifactKind.IMAGE,
                locator=str(canonical_url),
                source=source,
                description=str(result.get("title") or "") or None,
            )
        )
    elif source == "hackernews" and canonical_url:
        artifacts.append(
            ArtifactRef(
                kind=ArtifactKind.THREAD,
                locator=str(canonical_url),
                source=source,
                description=str(result.get("title") or "") or None,
            )
        )
    elif source == "arxiv" and canonical_url:
        artifacts.append(
            ArtifactRef(
                kind=ArtifactKind.DOCUMENT,
                locator=str(canonical_url),
                source=source,
                description=str(result.get("title") or "") or None,
            )
        )

    source_id = _first(result, "id", "arxiv_id", "objectID")
    title = _first(result, "title")
    author = _author(result)
    published = _first(result, "published", "publishedDate", "created_at", "time")
    text = claim or _claim_text(result)
    if not str(text).strip():
        raise ValueError(f"{source} result contains no usable claim text")

    return EvidenceItem(
        source=source,
        claim=str(text),
        canonical_url=str(canonical_url) if canonical_url else None,
        source_id=str(source_id) if source_id else None,
        title=str(title) if title else None,
        author=author,
        published_at=str(published) if published else None,
        source_kind=source_kind,
        artifact_refs=tuple(artifacts),
        backend=backend,
        metadata=metadata,
    )


def _claim_text(result: Mapping[str, Any]) -> str:
    direct = _first(result, "summary", "snippet", "text")
    if direct:
        return str(direct)
    highlights = result.get("highlights")
    if isinstance(highlights, (list, tuple)):
        clean = [str(value) for value in highlights if value]
        if clean:
            return " ".join(clean)
    title = result.get("title")
    return str(title) if title else ""


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
