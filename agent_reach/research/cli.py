"""JSON-in/Markdown-out CLI for deterministic Research Edition runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import SourceKind
from .planner import ResearchPlan, ResearchQuestion
from .report import render_markdown
from .runner import ResearchRun
from .serialization import deserialize_run


def run_document(payload: dict) -> str:
    if payload.get("schema_version") == 1 and "plan" in payload:
        return render_markdown(deserialize_run(payload))

    questions = tuple(
        ResearchQuestion(
            text=q["text"],
            preferred_sources=tuple(q.get("preferred_sources", ())),
            require_primary_source=bool(q.get("require_primary_source", False)),
        )
        for q in payload["questions"]
    )
    plan = ResearchPlan(
        topic=payload["topic"],
        questions=questions,
        max_results_per_source=int(payload.get("max_results_per_source", 10)),
        minimum_independent_sources=int(payload.get("minimum_independent_sources", 2)),
    )
    run = ResearchRun(plan)
    for source, results in payload.get("results", {}).items():
        kind_value = payload.get("source_kinds", {}).get(source, "unknown")
        kind = SourceKind(kind_value)
        for result in results:
            from .adapters import evidence_from_result

            evidence_id = run.store.add(
                evidence_from_result(source, result, source_kind=kind)
            )
            for question in questions:
                if source in question.preferred_sources:
                    run.question_evidence.setdefault(question.text, set()).add(
                        evidence_id
                    )
    run.coverage_gaps.extend(payload.get("coverage_gaps", ()))
    return render_markdown(run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reach-research")
    parser.add_argument("input", type=Path, nargs="?", help="Research JSON document")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    if args.input is None:
        parser.print_help()
        return 0
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    rendered = run_document(payload)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0
