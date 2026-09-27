"""Serialization for replayable research runs."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .runner import ResearchRun
from .verification import derive_state


def serialize_run(run: ResearchRun) -> dict[str, Any]:
    evidence = []
    for item in run.store.all():
        payload = asdict(item)
        payload["source_kind"] = item.source_kind.value
        payload["state"] = derive_state(item, run.store).value
        payload["evidence_id"] = item.evidence_id
        evidence.append(payload)

    return {
        "schema_version": 1,
        "plan": asdict(run.plan),
        "coverage_gaps": list(run.coverage_gaps),
        "attempted_queries": run.attempted_queries,
        "successful_queries": run.successful_queries,
        "discarded_results": run.discarded_results,
        "evidence": evidence,
    }
