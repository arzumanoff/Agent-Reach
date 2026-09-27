from unittest.mock import patch

from agent_reach.research.github_live import github_repository_search


class Config:
    def __init__(self, token=None):
        self.token = token

    def get(self, key, default=None):
        if key == "github_token":
            return self.token
        return default


class Response:
    ok = True
    status_code = 200

    def json(self):
        return {
            "items": [
                {
                    "id": 1,
                    "full_name": "owner/repo",
                    "html_url": "https://github.com/owner/repo",
                    "description": "Research tool",
                    "stargazers_count": 123,
                    "updated_at": "2026-09-01T00:00:00Z",
                    "owner": {"login": "owner"},
                }
            ]
        }


def test_github_search_normalizes_results_and_uses_header_token():
    seen = {}

    def fake_get(url, *, params, headers, timeout):
        seen.update(url=url, params=params, headers=headers, timeout=timeout)
        return Response()

    with patch("agent_reach.research.github_live.requests.get", side_effect=fake_get):
        results = github_repository_search(Config("secret"))("agent reach", 5)

    assert results[0]["title"] == "owner/repo"
    assert results[0]["url"] == "https://github.com/owner/repo"
    assert seen["params"]["q"] == "agent reach"
    assert seen["headers"]["Authorization"] == "Bearer secret"
    assert "secret" not in seen["url"]


def test_github_search_caps_limit():
    seen = {}

    def fake_get(url, *, params, headers, timeout):
        seen["per_page"] = params["per_page"]
        return Response()

    with patch("agent_reach.research.github_live.requests.get", side_effect=fake_get):
        github_repository_search(Config())("query", 1000)

    assert seen["per_page"] == 30
