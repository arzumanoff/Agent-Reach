import json

from agent_reach.research.models import EvidenceItem
from agent_reach.research.planner import ResearchPlan, ResearchQuestion
from agent_reach.research.runner import ResearchRun
from agent_reach.research.serialization import serialize_run


def test_serialized_run_has_schema_and_stable_evidence_id():
    run = ResearchRun(ResearchPlan(topic="x", questions=(ResearchQuestion("q"),)))
    item = EvidenceItem(source="github", source_id="1", claim="claim")
    run.store.add(item)
    run.discarded_results = 2
    payload = serialize_run(run)
    assert payload["schema_version"] == 1
    assert payload["evidence"][0]["evidence_id"] == item.evidence_id
    assert payload["evidence"][0]["state"] == "single-source"
    assert payload["discarded_results"] == 2
    json.dumps(payload)
