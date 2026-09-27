from unittest.mock import patch

import pytest

from agent_reach.channels.hackernews import HackerNewsChannel


def test_search_rejects_empty_query():
    with pytest.raises(ValueError, match="must not be empty"):
        HackerNewsChannel().search("   ")


def test_search_caps_limit_to_100():
    seen = {}

    def fake_get(url):
        seen["url"] = url
        return {"hits": []}

    with patch("agent_reach.channels.hackernews._get_json", side_effect=fake_get):
        HackerNewsChannel().search("agent", limit=1000)
    assert "hitsPerPage=100" in seen["url"]


def test_story_list_rejects_wrong_shape():
    with patch("agent_reach.channels.hackernews._get_json", return_value={"bad": True}):
        with pytest.raises(ValueError, match="invalid JSON shape"):
            HackerNewsChannel().get_stories()


def test_item_rejects_wrong_shape():
    with patch("agent_reach.channels.hackernews._get_json", return_value=["bad"]):
        with pytest.raises(ValueError, match="invalid JSON shape"):
            HackerNewsChannel().get_item(1)


def test_user_rejects_wrong_shape():
    with patch("agent_reach.channels.hackernews._get_json", return_value=["bad"]):
        with pytest.raises(ValueError, match="invalid JSON shape"):
            HackerNewsChannel().get_user("user")
