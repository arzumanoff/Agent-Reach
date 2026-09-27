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
    question_evidence: dict[str, set[str]] = field(default_factory=dict)

    def collect(
        self,
        searches: Mapping[str, SearchFn],
        source_kinds: Mapping[str, SourceKind] | None = None,
    ) -> EvidenceStore:
        kinds = source_kinds or {}
        for question in self.plan.questions:
            evidence_ids = self.question_evidence.setdefault(question.text, set())
            for source in question.preferred_sources:
                search = searches.get(source)
                if search is None:
                    self.coverage_gaps.append(
                        f"{question.text} :: {source}: no search adapter"
                    )
                    continue

                self.attempted_queries += 1
                try:
                    results = search(question.text, self.plan.max_results_per_source)
                except Exception as exc:
                    self.coverage_gaps.append(
                        f"{question.text} :: {source}: {type(exc).__name__}"
                    )
                    continue

                if not results:
                    self.coverage_gaps.append(
                        f"{question.text} :: {source}: no results"
                    )
                    continue

                accepted = 0
                for result in results:
                    try:
                        item = evidence_from_result(
                            source,
                            result,
                            source_kind=kinds.get(source, SourceKind.UNKNOWN),
                        )
                    except (TypeError, ValueError) as exc:
                        self.discarded_results += 1
                        self.coverage_gaps.append(
                            f"{question.text} :: {source}: discarded "
                            f"{type(exc).__name__}"
                        )
                        continue
                    evidence_id = self.store.add(item)
                    evidence_ids.add(evidence_id)
                    accepted += 1

                if accepted:
                    self.successful_queries += 1
                else:
                    self.coverage_gaps.append(
                        f"{question.text} :: {source}: no usable results"
                    )

        return self.store
