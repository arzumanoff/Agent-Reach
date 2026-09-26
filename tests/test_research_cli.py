from agent_reach.research.cli import run_document


def test_replay_document_renders_evidence_and_gap():
    text = run_document(
        {
            "topic": "GPU",
            "questions": [{"text": "memory?", "preferred_sources": ["arxiv"]}],
            "source_kinds": {"arxiv": "primary"},
            "results": {
                "arxiv": [
                    {
                        "arxiv_id": "2601.1",
                        "title": "Paper",
                        "summary": "32 GB",
                        "link": "https://arxiv.org/abs/2601.1",
                    }
                ]
            },
            "coverage_gaps": ["github: unavailable"],
        }
    )
    assert "Research report: GPU" in text
    assert "32 GB" in text
    assert "github: unavailable" in text
