"""Deterministic reporting for research evidence."""

from __future__ import annotations

from .models import EvidenceState
from .policy import evaluate_policy
from .runner import ResearchRun
from .store import EvidenceStore
from .verification import derive_state


def build_summary(store: EvidenceStore) -> dict[str, int]:
    counts = {state.value: 0 for state in EvidenceState}
    for item in store.all():
        counts[derive_state(item, store).value] += 1
    counts["total"] = len(store)
    return counts


def render_markdown(run: ResearchRun) -> str:
    summary = build_summary(run.store)
    lines = [
        f"# Research report: {run.plan.topic}",
        "",
        "## Evidence summary",
        "",
        f"- Total: {summary['total']}",
    ]
    for state in EvidenceState:
        lines.append(f"- {state.value}: {summary[state.value]}")

    policy = evaluate_policy(run.plan, run.store)\n    lines.extend(["", "## Coverage policy", ""])\n    lines.append(f"- Satisfied: {str(policy.satisfied).lower()}")\n    lines.append(f"- Independent sources: {policy.independent_sources}")\n    lines.append(f"- Primary sources: {policy.primary_sources}")\n    for reason in policy.reasons:\n        lines.append(f"- Gap: {reason}")\n\n    lines.extend(["", "## Evidence", ""])
    for item in run.store.all():
        state = derive_state(item, run.store).value
        title = item.title or item.source_id or item.source
        provenance = item.canonical_url or item.source_id or "no stable locator"
        lines.extend([
            f"### [{state}] {title}",
            "",
            item.claim,
            "",
            f"Source: {item.source} | Locator: {provenance}",
            "",
        ])

    lines.extend(["## Coverage gaps", ""])
    if run.coverage_gaps:
        lines.extend(f"- {gap}" for gap in run.coverage_gaps)
    else:
        lines.append("- None recorded")
    lines.append("")
    return "\n".join(lines)
