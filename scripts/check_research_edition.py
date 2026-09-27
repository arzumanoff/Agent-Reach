"""Fast local quality gate for Research Edition source files."""

from __future__ import annotations

import compileall
import importlib
import sys

MODULES = (
    "agent_reach.channels.arxiv",
    "agent_reach.channels.duckduckgo",
    "agent_reach.channels.google_images",
    "agent_reach.channels.hackernews",
    "agent_reach.channels.tiktok",
    "agent_reach.channels.youtube",
    "agent_reach.exa_api",
    "agent_reach.transcribe",
    "agent_reach.research",
    "agent_reach.research.adapters",
    "agent_reach.research.artifacts",
    "agent_reach.research.cli",
    "agent_reach.research.contradictions",
    "agent_reach.research.corroboration",
    "agent_reach.research.guard",
    "agent_reach.research.live",
    "agent_reach.research.models",
    "agent_reach.research.orchestrator",
    "agent_reach.research.planner",
    "agent_reach.research.policy",
    "agent_reach.research.report",
    "agent_reach.research.runner",
    "agent_reach.research.semantic",
    "agent_reach.research.serialization",
    "agent_reach.research.store",
    "agent_reach.research.trust",
    "agent_reach.research.verification",
)


def main() -> int:
    if not compileall.compile_dir("agent_reach", quiet=1):
        print("compileall failed", file=sys.stderr)
        return 1
    for module in MODULES:
        importlib.import_module(module)
    print(f"Research Edition smoke gate passed ({len(MODULES)} imports)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
