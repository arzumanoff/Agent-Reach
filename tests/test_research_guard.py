import pytest

from agent_reach.research.guard import reject_secret_path, validate_research_url


@pytest.mark.parametrize("url", [
    "https://export.arxiv.org/api/query",
    "https://hn.algolia.com/api/v1/search",
    "https://api.github.com/repos/openai/openai",
])
def test_known_research_destinations_allowed(url):
    assert validate_research_url(url) == url


@pytest.mark.parametrize("url", [
    "http://hn.algolia.com/api/v1/search",
    "https://evil.example/collect",
    "https://hn.algolia.com.evil.example/x",
    "https://user:pass@github.com/x",
])
def test_unknown_or_unsafe_destinations_fail_closed(url):
    with pytest.raises(ValueError):
        validate_research_url(url)


@pytest.mark.parametrize("path", [
    "~/.agent-reach/config.yaml",
    "~/.ssh/id_ed25519",
    "C:\\Users\\me\\.aws\\credentials",
    ".env",
])
def test_secret_paths_rejected(path):
    with pytest.raises(ValueError):
        reject_secret_path(path)
