"""Canonical integration artifacts shared between verification and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.schemas import EvaluationResult
from verification import FailureFingerprinter, VerificationResult


@dataclass(frozen=True)
class VerifiedFailureArtifact:
    """A verified canonical failure ready for permanent persistence.

    This deliberately carries the existing engine objects rather than defining
    a competing evaluation or fingerprint schema.
    """

    evaluation: EvaluationResult
    verification: VerificationResult
    failure_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation, EvaluationResult):
            raise TypeError("evaluation must be an EvaluationResult")
        if not isinstance(self.verification, VerificationResult):
            raise TypeError("verification must be a VerificationResult")
        if self.evaluation.status != "failure":
            raise ValueError("only failing evaluations can form a verified failure artifact")
        if not self.verification.verified:
            raise ValueError("only verified failures can form a verified failure artifact")
        if self.verification.original_evaluation_id != self.evaluation.evaluation_id:
            raise ValueError("verification result does not belong to the evaluation")
        expected = FailureFingerprinter().generate(self.evaluation)
        if self.failure_fingerprint != expected:
            raise ValueError("failure_fingerprint must match the canonical EvaluationResult")

    @classmethod
    def from_verification(
        cls,
        evaluation: EvaluationResult,
        verification: VerificationResult,
        *,
        fingerprinter: FailureFingerprinter | None = None,
    ) -> "VerifiedFailureArtifact":
        """Build an artifact using the engine's canonical fingerprinter."""
        fingerprint = (fingerprinter or FailureFingerprinter()).generate(evaluation)
        return cls(
            evaluation=evaluation,
            verification=verification,
            failure_fingerprint=fingerprint,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable handoff representation."""
        return {
            "failure_fingerprint": self.failure_fingerprint,
            "evaluation": self.evaluation.to_dict(),
            "verification": self.verification.to_dict(include_results=False),
        }


class ReleaseVerdict(str, Enum):
    """Product-level release vocabulary."""

    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class PublicSeverity(str, Enum):
    """Product-level severity vocabulary at the persistence/release boundary."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class ModelIdentity:
    """Stable model identity carried into a product release decision."""

    model_id: str
    name: str
    version: str


@dataclass(frozen=True)
class ReleaseFinding:
    """One deterministic policy assessment of verified failure evidence."""

    failure_fingerprint: str
    severity: PublicSeverity
    internal_policy: str
    observed_score: float
    minimum_threshold: float
    status: str


@dataclass(frozen=True)
class ReleaseDecision:
    """Canonical, serializable release outcome derived from verified evidence."""

    verdict: ReleaseVerdict
    rationale: str
    evaluated_findings: int
    verified_failures: int
    highest_severity: PublicSeverity | None
    triggering_failure_fingerprints: tuple[str, ...]
    candidate: ModelIdentity
    baseline: ModelIdentity
    findings: tuple[ReleaseFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a machine-readable product release decision."""
        return {
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "evaluated_findings": self.evaluated_findings,
            "verified_failures": self.verified_failures,
            "highest_severity": self.highest_severity.value if self.highest_severity else None,
            "triggering_failure_fingerprints": list(self.triggering_failure_fingerprints),
            "candidate": self.candidate.__dict__,
            "baseline": self.baseline.__dict__,
            "findings": [
                {
                    "failure_fingerprint": finding.failure_fingerprint,
                    "severity": finding.severity.value,
                    "internal_policy": finding.internal_policy,
                    "observed_score": finding.observed_score,
                    "minimum_threshold": finding.minimum_threshold,
                    "status": finding.status,
                }
                for finding in self.findings
            ],
        }
