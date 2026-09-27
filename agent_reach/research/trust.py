"""Trust-boundary helpers for untrusted retrieved content.

The research layer never treats retrieved text as instructions. These helpers label
and bound content before it is handed to an agent/model.
"""

from __future__ import annotations

from dataclasses import dataclass

_MAX_UNTRUSTED_CHARS = 100_000


@dataclass(frozen=True)
class UntrustedContent:
    text: str
    source: str
    truncated: bool = False

    def as_prompt_data(self) -> str:
        return (
            "<untrusted-retrieved-content source="
            + repr(self.source)
            + ">\n"
            + self.text
            + "\n</untrusted-retrieved-content>"
        )


def bound_untrusted_text(text: str, source: str, limit: int = _MAX_UNTRUSTED_CHARS) -> UntrustedContent:
    if limit < 1:
        raise ValueError("limit must be positive")
    if len(text) <= limit:
        return UntrustedContent(text=text, source=source)
    return UntrustedContent(text=text[:limit], source=source, truncated=True)
