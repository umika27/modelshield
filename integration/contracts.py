"""Canonical integration artifacts shared between verification and persistence."""

from __future__ import annotations

from dataclasses import dataclass
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
