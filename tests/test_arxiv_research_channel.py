import pytest

from agent_reach.channels.arxiv import ArxivChannel


def test_search_rejects_empty_query():
    with pytest.raises(ValueError, match="must not be empty"):
        ArxivChannel().search("   ")


def test_get_paper_rejects_empty_id():
    with pytest.raises(ValueError, match="must not be empty"):
        ArxivChannel().get_paper("   ")
