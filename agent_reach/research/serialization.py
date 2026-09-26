"""Serialization for replayable research runs."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .runner import ResearchRun
from .verification import derive_state


def serialize_run(run: ResearchRun) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "plan": asdict(run.plan),
        "coverage_gaps": list(run.coverage_gaps),
        "evidence": [
            {
                **asdict(item),
                "source_kind": item.source_kind.value,
                "state": derive_state(item, run.store).value,
                "evidence_id": item.evidence_id,
            }
            for item in run.store.all()
        ],
    }
