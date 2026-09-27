"""Fail-closed policy for research-side network destinations and local secrets."""

from __future__ import annotations

from pathlib import PurePath
from urllib.parse import urlsplit

_ALLOWED_RESEARCH_HOSTS = frozenset({
    "arxiv.org",
    "export.arxiv.org",
    "hacker-news.firebaseio.com",
    "hn.algolia.com",
    "news.ycombinator.com",
    "github.com",
    "api.github.com",
    "api.exa.ai",
    "www.googleapis.com",
    "reddit.com",
    "www.reddit.com",
    "youtube.com",
    "www.youtube.com",
    "bilibili.com",
    "www.bilibili.com",
    "jina.ai",
    "r.jina.ai",
})

_SECRET_COMPONENTS = frozenset({
    ".ssh", ".aws", ".env", "config.yaml", ".grimdall-key",
})


def validate_research_url(url: str) -> str:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid research URL") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not host or port not in (None, 443):
        raise ValueError("research URL must use HTTPS on the default port")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("research URL must not contain credentials")
    if not any(host == allowed or host.endswith("." + allowed) for allowed in _ALLOWED_RESEARCH_HOSTS):
        raise ValueError(f"research destination is not allowlisted: {host}")
    return url


def reject_secret_path(path: str) -> str:
    normalized = path.replace("\\", "/").lower()
    parts = {part for part in PurePath(normalized).parts if part}
    if ".agent-reach/config.yaml" in normalized:
        raise ValueError("research operation must not read Agent-Reach credentials")
    if parts.intersection(_SECRET_COMPONENTS):
        raise ValueError("research operation must not read secret-bearing paths")
    return path
