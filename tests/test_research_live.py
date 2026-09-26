from agent_reach.research.live import arxiv_search, hackernews_search


class Arxiv:
    def search(self, query, limit=10):
        return [{"title": query, "limit": limit}]


class HN:
    def search(self, query, limit=10):
        return [{"title": query, "limit": limit}]


def test_arxiv_adapter_matches_runner_contract():
    assert arxiv_search(Arxiv())("paper", 3)[0]["limit"] == 3


def test_hn_adapter_matches_runner_contract():
    assert hackernews_search(HN())("agent", 4)[0]["limit"] == 4
