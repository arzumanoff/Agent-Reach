"""Typed references to non-text research artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArtifactKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    CODE = "code"
    DOCUMENT = "document"
    THREAD = "thread"


@dataclass(frozen=True)
class ArtifactRef:
    kind: ArtifactKind
    locator: str
    source: str
    description: str | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.locator.strip():
            raise ValueError("artifact locator must not be empty")
        if not self.source.strip():
            raise ValueError("artifact source must not be empty")
