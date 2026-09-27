"""Deterministic research-run orchestration over pluggable search callables."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .adapters import evidence_from_result
from .models import SourceKind
from .planner import ResearchPlan
from .store import EvidenceStore

SearchFn = Callable[[str, int], Sequence[Mapping[str, Any]]]


@dataclass
class ResearchRun:
    plan: ResearchPlan
    store: EvidenceStore = field(default_factory=EvidenceStore)
    coverage_gaps: list[str] = field(default_factory=list)
    attempted_queries: int = 0
    successful_queries: int = 0
    discarded_results: int = 0

    def collect(
        self,
        searches: Mapping[str, SearchFn],
        source_kinds: Mapping[str, SourceKind] | None = None,
    ) -> EvidenceStore:
        kinds = source_kinds or {}
        for question in self.plan.questions:
            for source in question.preferred_sources:
                search = searches.get(source)
                if search is None:
                    self.coverage_gaps.append(f"{source}: no search adapter")
                    continue

                self.attempted_queries += 1
                try:
                    results = search(question.text, self.plan.max_results_per_source)
                except Exception as exc:
                    self.coverage_gaps.append(f"{source}: {type(exc).__name__}")
                    continue

                if not results:
                    self.coverage_gaps.append(
                        f"{source}: no results for {question.text!r}"
                    )
                    continue

                self.successful_queries += 1
                accepted = 0
                for result in results:
                    if not isinstance(result, Mapping):
                        self.discarded_results += 1
                        continue
                    try:
                        item = evidence_from_result(
                            source,
                            result,
                            source_kind=kinds.get(source, SourceKind.UNKNOWN),
                        )
                    except (TypeError, ValueError):
                        self.discarded_results += 1
                        continue
                    self.store.add(item)
                    accepted += 1
                if accepted == 0:
                    self.coverage_gaps.append(
                        f"{source}: results contained no usable evidence for {question.text!r}"
                    )
        return self.store
