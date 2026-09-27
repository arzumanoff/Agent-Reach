"""Data model for provenance-preserving research evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .artifacts import ArtifactRef


class EvidenceState(str, Enum):
    CONFIRMED = "confirmed"
    CORROBORATED = "corroborated"
    SINGLE_SOURCE = "single-source"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"


class SourceKind(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceItem:
    source: str
    claim: str
    canonical_url: str | None = None
    source_id: str | None = None
    title: str | None = None
    author: str | None = None
    published_at: str | None = None
    source_kind: SourceKind = SourceKind.UNKNOWN
    state: EvidenceState = EvidenceState.UNVERIFIED
    artifact_refs: tuple[ArtifactRef, ...] = ()
    corroborates: tuple[str, ...] = ()
    contradicts: tuple[str, ...] = ()
    backend: str | None = None
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("evidence source must not be empty")
        if not self.claim.strip():
            raise ValueError("evidence claim must not be empty")

    @property
    def evidence_id(self) -> str:
        """Stable ID based on source identity and normalized claim."""
        identity = self.canonical_url or self.source_id or self.source
        normalized_identity = _normalize_identity(str(identity))
        normalized_claim = " ".join(self.claim.split()).casefold()
        raw = f"{normalized_identity}\n{normalized_claim}".encode("utf-8")
        return sha256(raw).hexdigest()[:20]


def _normalize_identity(identity: str) -> str:
    value = " ".join(identity.split())
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value.casefold()
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname.lower().rstrip(".")
        port = parsed.port
        netloc = host if port in (None, 80, 443) else f"{host}:{port}"
        return urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path, parsed.query, "")
        )
    return value.casefold()
