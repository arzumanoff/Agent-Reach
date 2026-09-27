"""Research planning contracts independent from any particular LLM."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchQuestion:
    text: str
    preferred_sources: tuple[str, ...] = ()
    require_primary_source: bool = False

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("research question must not be empty")
        if any(not source.strip() for source in self.preferred_sources):
            raise ValueError("preferred source names must not be empty")


@dataclass(frozen=True)
class ResearchPlan:
    topic: str
    questions: tuple[ResearchQuestion, ...]
    max_results_per_source: int = 10
    minimum_independent_sources: int = 2
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not self.questions:
            raise ValueError("at least one research question is required")
        question_texts = [question.text.strip() for question in self.questions]
        if len(set(question_texts)) != len(question_texts):
            raise ValueError("research question text must be unique")
        if self.max_results_per_source < 1:
            raise ValueError("max_results_per_source must be positive")
        if self.minimum_independent_sources < 1:
            raise ValueError("minimum_independent_sources must be positive")

    @property
    def requested_sources(self) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for question in self.questions:
            for source in question.preferred_sources:
                seen.setdefault(source, None)
        return tuple(seen)
