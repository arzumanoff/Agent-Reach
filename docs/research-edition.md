# Agent-Reach Research Edition

This branch develops an evidence-first deep-research layer on top of Agent-Reach while keeping `main` close to upstream.

## Goals

- Keep upstream Agent-Reach updateable.
- Add research orchestration without coupling it to individual channels.
- Treat retrieved web content as untrusted input.
- Preserve source provenance from discovery through the final report.
- Support Windows/Codex as a first-class environment.
- Prefer multiple interchangeable backends over hard dependencies.

## Proposed pipeline

```text
Research request
  -> Research Planner
  -> Query/Source Router
  -> Agent-Reach channels/backends
  -> Safety/Sanitization boundary
  -> Evidence Collector
  -> Normalization + Deduplication
  -> Corroboration / Contradiction analysis
  -> Evidence grading
  -> Research report with provenance
```

## Evidence model (v0)

Each evidence item should retain at minimum:

- canonical URL / source identifier
- source/channel
- title/author/date when available
- retrieval timestamp
- extracted claim or observation
- direct vs. secondary source classification
- supporting artifact references (image/video/code/thread)
- corroborating and contradicting evidence IDs
- confidence state: `confirmed`, `corroborated`, `single-source`, `unverified`, `contradicted`
- retrieval/backend metadata

Confidence is an evidence state, not an LLM probability.

## Integration policy

External PRs/forks are not bulk-merged. For every candidate:

1. Check whether current upstream already contains or supersedes it.
2. Review security and dependency impact.
3. Port the smallest useful change.
4. Add/retain tests.
5. Keep channel-specific code outside the research core.

Initial candidates to review include Hacker News, arXiv, research orchestration, prompt-injection/cookie guardrails, Exa REST/fallback search, Windows fixes, browser multi-profile handling, YouTube diagnostics, image search and additional video/social channels.

## Milestones

### R0 — Baseline and audit
- Record upstream baseline.
- Re-audit open PRs against current upstream.
- Define stable research interfaces and threat model.

### R1 — Research core
- Planner contract.
- Evidence schema/store.
- Deduplication.
- Provenance-preserving report output.

### R2 — Verification
- Corroboration and contradiction detection.
- Primary-source preference.
- Evidence grading.
- Source diversity controls.

### R3 — Channels/backends
- Integrate selected missing sources and Windows fixes only after audit.
- Add backend fallback/health semantics.

### R4 — Codex skill
- Natural-language deep-research entry point.
- Progress/events.
- Reproducible research runs.
- Windows installation and diagnostics.

## Non-goals for the first iteration

- UI/dashboard.
- Autonomous account actions.
- Posting or modifying content on external platforms.
- Blindly merging every community PR.
- Replacing Agent-Reach's channel/backend architecture.
