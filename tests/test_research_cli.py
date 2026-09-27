from agent_reach.research.cli import run_document, run_live_document


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


def test_live_document_executes_plan_with_injected_sources():
    from agent_reach.research.models import SourceKind

    payload = {
        "topic": "GPU",
        "questions": [
            {
                "text": "memory?",
                "preferred_sources": ["official", "community"],
                "require_primary_source": True,
            }
        ],
        "minimum_independent_sources": 2,
    }
    searches = {
        "official": lambda q, n: [
            {
                "url": "https://vendor.example/spec",
                "title": "Spec",
                "text": "32 GB",
            }
        ],
        "community": lambda q, n: [
            {
                "url": "https://forum.example/thread",
                "title": "Thread",
                "text": "32 GB",
            }
        ],
    }
    run, report = run_live_document(
        payload,
        searches,
        {
            "official": SourceKind.PRIMARY,
            "community": SourceKind.COMMUNITY,
        },
    )

    assert len(run.store) == 2
    assert run.attempted_queries == 2
    assert run.successful_queries == 2
    assert "Satisfied: true" in report
