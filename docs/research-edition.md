# Agent-Reach Research Edition

Research Edition is an evidence-first deep-research layer built on Agent-Reach.
The fork keeps `main` aligned with upstream and develops the research stack on
`research-edition`.

## Current pipeline

```text
ResearchPlan
  -> live source adapters
  -> ResearchRun
  -> EvidenceStore
  -> exact + constrained semantic relations
  -> corroboration / contradiction graph
  -> source-identity + primary-source policy
  -> provenance-rich Markdown report
  -> replayable JSON serialization
```

Retrieved internet content is treated as untrusted data, never as instructions.

## Install the branch

```bash
python -m pip install --upgrade   "https://github.com/arzumanoff/Agent-Reach/archive/refs/heads/research-edition.zip"
```

Optional DuckDuckGo fallback:

```bash
python -m pip install -U ddgs
```

Then inspect available channels:

```bash
agent-reach doctor --json
```

## Research sources added by this branch

- Hacker News — Firebase + Algolia, no key.
- ArXiv — public Atom API, no key.
- DuckDuckGo — optional maintained `ddgs` package.
- TikTok — public-video read via yt-dlp, browser-backed search via OpenCLI.
- Google Images — official Custom Search JSON API.
- Exa — optional direct REST transport plus existing MCP fallback.

Existing Agent-Reach sources remain available.

## Configure optional search backends

Exa direct REST:

```bash
agent-reach configure exa-key
```

Google Images:

```bash
agent-reach configure google-key
agent-reach configure google-cx
```

Sensitive values are rejected when passed positionally. Use the hidden prompt
or `--stdin`.

## Replayable research

`agent-reach-research` accepts either a prepared research document or the
serialized schema emitted by `serialize_run()`.

```bash
agent-reach-research research.json
agent-reach-research research.json -o report.md
```

The serialized schema preserves:

- plan and research questions
- evidence + stable IDs
- source kind and derived evidence state
- typed artifacts
- corroboration / contradiction links
- per-question evidence coverage
- coverage gaps
- attempted/successful query counts
- discarded malformed results

## Python orchestration

```python
from agent_reach.research import (
    ResearchPlan,
    ResearchQuestion,
    SourceKind,
    execute_research,
)
from agent_reach.research.live import (
    arxiv_search,
    hackernews_search,
    duckduckgo_search,
)

plan = ResearchPlan(
    topic="Example investigation",
    questions=(
        ResearchQuestion(
            "What is independently documented?",
            ("arxiv", "hackernews", "duckduckgo"),
            require_primary_source=True,
        ),
    ),
    minimum_independent_sources=2,
)

run, policy, report = execute_research(
    plan,
    {
        "arxiv": arxiv_search(),
        "hackernews": hackernews_search(),
        "duckduckgo": duckduckgo_search(),
    },
    {
        "arxiv": SourceKind.PRIMARY,
        "hackernews": SourceKind.COMMUNITY,
        "duckduckgo": SourceKind.SECONDARY,
    },
)

print(report)
```

## Evidence states

- `confirmed` — at least two independent source identities corroborate the
  evidence cluster and at least one item is primary evidence.
- `corroborated` — independent support exists but the stricter confirmed gate
  is not met.
- `single-source` — identifiable evidence with no independent corroboration.
- `unverified` — insufficient stable provenance.
- `contradicted` — explicit contradictory evidence is linked.

These states describe the collected evidence, not absolute truth and not an LLM
probability.

## Independence rules

Transport is not publisher identity.

For example:

- Exa + Jina reading the same publisher does not count as two sources.
- Two URLs on the same publisher host count conservatively as one identity.
- Hacker News discussion evidence is attributed to the HN thread, while its
  linked article is stored separately.
- Google Images evidence uses the context page for provenance and stores the
  image itself as an `IMAGE` artifact.

## Security boundaries

- Retrieved text is explicitly delimited as untrusted content.
- Research URL destinations can be fail-closed through the research guard.
- Secret-bearing local paths are rejected.
- API-key-bearing transport errors are scrubbed.
- Positional CLI secrets are rejected.
- Research Edition does not auto-execute instructions found in webpages,
  posts, comments, transcripts, or papers.

The large Grimdall PR was not bulk-merged because its static egress allowlist
was already stale for the expanded source set and its default shadow mode still
executes flagged commands. Research Edition keeps a narrower fail-closed
research boundary instead.

## Windows / Codex work

The branch includes selected Windows/restricted-environment fixes:

- yt-dlp config follows `HOME` consistently on Windows.
- extensionless `rdt` wrapper detection.
- restricted-sandbox chmod handling.
- OpenCLI multi-profile extension detection.
- MCP doctor probes are moved off the event loop.
- YouTube JS-runtime comment parsing.
- validated/scoped YouTube browser-cookie forwarding.

## Quality gate

The branch contains `.github/workflows/research-edition.yml` with:

- Windows + Linux
- Python 3.10 / 3.12 / 3.13
- compile/import smoke gate
- pytest
- Ruff
- mypy
- wheel build
- CLI smoke tests

On forks, GitHub may require Actions to be enabled manually before the first
workflow run appears.

## Upstream integration policy

Community PRs are never bulk-merged. For each candidate:

1. Check whether upstream already contains or supersedes it.
2. Review security and dependency impact.
3. Port the smallest useful change.
4. Add focused regression coverage.
5. Keep channel-specific code outside the research core.

Serenity was intentionally not imported wholesale: it is an 80-file,
industry/finance application. Research Edition adopted the reusable concepts
(typed evidence, coverage gaps, deterministic export, evidence-gated states)
without importing its UI, valuation, or finance-specific stack.

## Non-goals for this iteration

- Autonomous account actions.
- Posting/commenting/liking.
- A dashboard/UI.
- Trading or financial decision automation.
- Treating community consensus as primary evidence.
