"""Adapters that connect stable ModelShield subsystems without changing them."""

from .contracts import (
    ModelIdentity,
    PublicSeverity,
    ReleaseDecision,
    ReleaseFinding,
    ReleaseVerdict,
    VerifiedFailureArtifact,
)
from .failure_memory_adapter import FailureMemoryAdapter
from .release_adapter import ReleaseDecisionAdapter, ReleaseEvidence, map_internal_policy, normalize_severity

__all__ = [
    "FailureMemoryAdapter",
    "ModelIdentity",
    "PublicSeverity",
    "ReleaseDecision",
    "ReleaseDecisionAdapter",
    "ReleaseEvidence",
    "ReleaseFinding",
    "ReleaseVerdict",
    "VerifiedFailureArtifact",
    "map_internal_policy",
    "normalize_severity",
]
