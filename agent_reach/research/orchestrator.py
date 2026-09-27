"""High-level orchestration for a complete Research Edition run."""

from __future__ import annotations

from collections.abc import Mapping

from .corroboration import link_exact_claims
from .models import SourceKind
from .planner import ResearchPlan
from .policy import PolicyResult, evaluate_policy
from .report import render_markdown
from .runner import ResearchRun, SearchFn


def execute_research(
    plan: ResearchPlan,
    searches: Mapping[str, SearchFn],
    source_kinds: Mapping[str, SourceKind] | None = None,
) -> tuple[ResearchRun, PolicyResult, str]:
    run = ResearchRun(plan)
    run.collect(searches, source_kinds)
    run.store = link_exact_claims(run.store)
    policy = evaluate_policy(plan, run.store, run.question_evidence)
    report = render_markdown(run)
    return run, policy, report
