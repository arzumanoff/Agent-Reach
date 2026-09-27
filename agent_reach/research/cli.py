"""CLI for live and replayable Agent-Reach Research Edition runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agent_reach.config import Config

from .live import build_live_sources
from .models import SourceKind
from .orchestrator import execute_research
from .planner import ResearchPlan, ResearchQuestion
from .report import render_markdown
from .runner import ResearchRun, SearchFn
from .serialization import deserialize_run, serialize_run


def plan_from_document(payload: dict[str, Any]) -> ResearchPlan:
    raw_plan = payload.get("plan") if isinstance(payload.get("plan"), dict) else payload
    raw_questions = raw_plan.get("questions")
    if not isinstance(raw_questions, (list, tuple)):
        raise ValueError("research document must contain questions")

    questions = tuple(
        ResearchQuestion(
            text=str(q["text"]),
            preferred_sources=tuple(q.get("preferred_sources", ())),
            require_primary_source=bool(q.get("require_primary_source", False)),
        )
        for q in raw_questions
        if isinstance(q, dict) and "text" in q
    )
    return ResearchPlan(
        topic=str(raw_plan.get("topic", "")),
        questions=questions,
        max_results_per_source=int(raw_plan.get("max_results_per_source", 10)),
        minimum_independent_sources=int(
            raw_plan.get("minimum_independent_sources", 2)
        ),
        notes=tuple(raw_plan.get("notes", ())),
    )


def run_document(payload: dict[str, Any]) -> str:
    if payload.get("schema_version") == 1 and "plan" in payload:
        return render_markdown(deserialize_run(payload))

    plan = plan_from_document(payload)
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


def run_live_document(
    payload: dict[str, Any],
    searches: dict[str, SearchFn],
    source_kinds: dict[str, SourceKind],
) -> tuple[ResearchRun, str]:
    plan = plan_from_document(payload)
    run, _policy, report = execute_research(plan, searches, source_kinds)
    return run, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-reach-research")
    parser.add_argument("input", type=Path, nargs="?", help="Research JSON document")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Execute the plan against configured live research sources",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="With --live, save a replayable JSON snapshot",
    )
    args = parser.parse_args(argv)

    if args.input is None:
        parser.print_help()
        return 0
    if args.snapshot and not args.live:
        parser.error("--snapshot requires --live")

    payload = json.loads(args.input.read_text(encoding="utf-8"))

    if args.live:
        config = Config(read_only=True)
        searches, source_kinds = build_live_sources(config)
        run, rendered = run_live_document(payload, searches, source_kinds)
        if args.snapshot:
            args.snapshot.write_text(
                json.dumps(serialize_run(run), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    else:
        rendered = run_document(payload)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0
