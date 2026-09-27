"""CLI for live and replayable Agent-Reach Research Edition runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .live import execute_live_research
from .models import SourceKind
from .planner import ResearchPlan, ResearchQuestion
from .report import render_markdown
from .runner import ResearchRun
from .serialization import deserialize_run, serialize_run


def _plan_from_payload(payload: dict[str, Any]) -> ResearchPlan:
    questions = tuple(
        ResearchQuestion(
            text=str(question["text"]),
            preferred_sources=tuple(question.get("preferred_sources", ())),
            require_primary_source=bool(
                question.get("require_primary_source", False)
            ),
        )
        for question in payload["questions"]
    )
    return ResearchPlan(
        topic=str(payload["topic"]),
        questions=questions,
        max_results_per_source=int(payload.get("max_results_per_source", 10)),
        minimum_independent_sources=int(
            payload.get("minimum_independent_sources", 2)
        ),
        notes=tuple(payload.get("notes", ())),
    )


def run_document(payload: dict[str, Any]) -> str:
    """Render either a serialized run or a legacy prepared-results document."""
    if payload.get("schema_version") == 1 and "plan" in payload:
        return render_markdown(deserialize_run(payload))

    plan = _plan_from_payload(payload)
    run = ResearchRun(plan)
    for source, results in payload.get("results", {}).items():
        kind_value = payload.get("source_kinds", {}).get(source, "unknown")
        kind = SourceKind(kind_value)
        for result in results:
            from .adapters import evidence_from_result

            evidence_id = run.store.add(
                evidence_from_result(source, result, source_kind=kind)
            )
            for question in plan.questions:
                if source in question.preferred_sources:
                    run.question_evidence.setdefault(question.text, set()).add(
                        evidence_id
                    )
    run.coverage_gaps.extend(payload.get("coverage_gaps", ()))
    return render_markdown(run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reach-research")
    parser.add_argument("input", type=Path, nargs="?", help="Research JSON document")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute the input plan against currently available structured backends",
    )
    parser.add_argument(
        "--save-json",
        type=Path,
        help="With --live, save the replayable ResearchRun JSON document",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write Markdown report")
    args = parser.parse_args(argv)

    if args.input is None:
        parser.print_help()
        return 0
    if args.save_json is not None and not args.live:
        parser.error("--save-json requires --live")

    payload = json.loads(args.input.read_text(encoding="utf-8"))

    if args.live:
        if payload.get("schema_version") == 1:
            parser.error("--live expects a plan document, not a serialized run")
        plan = _plan_from_payload(payload)
        run, _policy, rendered = execute_live_research(plan)
        if args.save_json is not None:
            args.save_json.write_text(
                json.dumps(
                    serialize_run(run),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
    else:
        rendered = run_document(payload)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0
