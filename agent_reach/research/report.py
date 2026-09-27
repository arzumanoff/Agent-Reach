"""Deterministic reporting for research evidence."""

from __future__ import annotations

from .models import EvidenceState
from .policy import evaluate_policy, source_identity
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
        "## Execution",
        "",
        f"- Queries attempted: {run.attempted_queries}",
        f"- Queries with results: {run.successful_queries}",
        f"- Results discarded: {run.discarded_results}",
        "",
        "## Evidence summary",
        "",
        f"- Total: {summary['total']}",
    ]
    for summary_state in EvidenceState:
        lines.append(f"- {summary_state.value}: {summary[summary_state.value]}")

    policy = evaluate_policy(run.plan, run.store, run.question_evidence or None)
    lines.extend(["", "## Coverage policy", ""])
    lines.append(f"- Satisfied: {str(policy.satisfied).lower()}")
    lines.append(f"- Independent sources: {policy.independent_sources}")
    lines.append(f"- Primary sources: {policy.primary_sources}")
    for reason in policy.reasons:
        lines.append(f"- Gap: {reason}")

    lines.extend(["", "## Question coverage", ""])
    for question in run.plan.questions:
        ids = run.question_evidence.get(question.text, set())
        items = [
            item
            for evidence_id in sorted(ids)
            if (item := run.store.get(evidence_id)) is not None
        ]
        identities = {source_identity(item) for item in items}
        lines.extend(
            [
                f"### {question.text}",
                f"- Evidence items: {len(items)}",
                f"- Independent source identities: {len(identities)}",
            ]
        )

    lines.extend(["", "## Evidence", ""])
    for item in run.store.all():
        item_state = derive_state(item, run.store).value
        title = item.title or item.source_id or item.source
        provenance = item.canonical_url or item.source_id or "no stable locator"
        lines.extend(
            [
                f"### [{item_state}] {title}",
                "",
                item.claim,
                "",
                f"Source: {item.source} | Locator: {provenance}",
            ]
        )
        if item.corroborates:
            lines.append("Corroborates: " + ", ".join(item.corroborates))
        if item.contradicts:
            lines.append("Contradicts: " + ", ".join(item.contradicts))
        lines.append("")

    lines.extend(["## Coverage gaps", ""])
    if run.coverage_gaps:
        lines.extend(f"- {gap}" for gap in run.coverage_gaps)
    else:
        lines.append("- None recorded")
    lines.append("")
    return "\n".join(lines)
