"""Evidence-first research primitives for Agent-Reach Research Edition."""

from .corroboration import link_exact_claims
from .models import EvidenceItem, EvidenceState, SourceKind
from .planner import ResearchPlan, ResearchQuestion
from .runner import ResearchRun
from .store import EvidenceStore

__all__ = [
    "EvidenceItem",
    "EvidenceState",
    "EvidenceStore",
    "ResearchPlan",
    "ResearchQuestion",
    "ResearchRun",
    "SourceKind",
    "link_exact_claims",
]
