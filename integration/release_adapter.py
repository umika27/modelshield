"""Deterministic bridge from verified failures to product release decisions.

The policy mirrors Kartikay's ``regression/policy.py`` and the default
compiler behavior in ``regression/runner.py`` without importing that branch's
conflicting ``core.schemas`` package. It consumes evidence only; model
execution remains the responsibility of the canonical engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .contracts import (
    ModelIdentity,
    PublicSeverity,
    ReleaseDecision,
    ReleaseFinding,
    ReleaseVerdict,
    VerifiedFailureArtifact,
)
from .failure_memory_adapter import classify_failure_memory_severity


_SEVERITY_ORDER = {
    PublicSeverity.LOW: 1,
    PublicSeverity.MEDIUM: 2,
    PublicSeverity.HIGH: 3,
    PublicSeverity.CRITICAL: 4,
}


@dataclass(frozen=True)
class ReleaseEvidence:
    """Verified performance evidence suitable for deterministic policy review."""

    failure_fingerprint: str
    baseline_score: float
    candidate_score: float
    severity: PublicSeverity
    verified: bool
    candidate: ModelIdentity
    baseline: ModelIdentity

    def __post_init__(self) -> None:
        if not self.failure_fingerprint.startswith("sha256:"):
            raise ValueError("failure_fingerprint must be a canonical sha256 fingerprint")
        for field_name in ("baseline_score", "candidate_score"):
            value = float(getattr(self, field_name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
            object.__setattr__(self, field_name, value)

    @classmethod
    def from_artifact(cls, artifact: VerifiedFailureArtifact) -> "ReleaseEvidence":
        """Convert the canonical Stage 1 artifact without recalculating evidence."""
        if not isinstance(artifact, VerifiedFailureArtifact):
            raise TypeError("artifact must be a VerifiedFailureArtifact")
        result = artifact.evaluation
        return cls(
            failure_fingerprint=artifact.failure_fingerprint,
            baseline_score=result.baseline_score,
            candidate_score=result.candidate_score,
            severity=normalize_severity(classify_failure_memory_severity(result.delta)),
            verified=artifact.verification.verified,
            candidate=_identity(result.candidate),
            baseline=_identity(result.baseline),
        )

    @classmethod
    def from_failure_memory(
        cls,
        record: Mapping[str, Any],
        *,
        candidate: ModelIdentity,
        baseline: ModelIdentity,
    ) -> "ReleaseEvidence":
        """Convert a retrieved FailureMemoryAdapter record for policy evaluation.

        Stage 1's SQLite Failure Memory does not persist the baseline identity,
        so callers explicitly supply the canonical comparison identities.
        """
        if not isinstance(record, Mapping):
            raise TypeError("record must be a mapping returned by FailureMemoryAdapter")
        try:
            return cls(
                failure_fingerprint=str(record["fingerprint"]),
                baseline_score=float(record["baseline_score"]),
                candidate_score=float(record["candidate_score"]),
                severity=normalize_severity(str(record["severity"])),
                verified=bool(record["verified"]),
                candidate=candidate,
                baseline=baseline,
            )
        except KeyError as exc:
            raise ValueError(f"Failure Memory record is missing {exc.args[0]!r}") from exc


def normalize_severity(value: str | PublicSeverity) -> PublicSeverity:
    """Map known subsystem labels into one deterministic public vocabulary.

    Failure Memory's ``minor/major/critical`` thresholds map to LOW/HIGH/
    CRITICAL.  No Failure Memory threshold represents MEDIUM, so the adapter
    never invents one; Kartikay's pre-existing ``medium`` label remains
    representable as MEDIUM when such evidence reaches this boundary.
    """
    normalized = value.value if isinstance(value, PublicSeverity) else value.lower()
    mapping = {
        "minor": PublicSeverity.LOW,
        "low": PublicSeverity.LOW,
        "medium": PublicSeverity.MEDIUM,
        "major": PublicSeverity.HIGH,
        "high": PublicSeverity.HIGH,
        "critical": PublicSeverity.CRITICAL,
    }
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise ValueError(f"unsupported severity {value!r}") from exc


def map_internal_policy(policy: str) -> ReleaseVerdict:
    """Translate Kartikay's allow/warn/block terms to product verdict names."""
    mapping = {
        "allow": ReleaseVerdict.PASS,
        "warn": ReleaseVerdict.REVIEW,
        "block": ReleaseVerdict.BLOCK,
    }
    try:
        return mapping[policy.lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported internal policy {policy!r}") from exc


class ReleaseDecisionAdapter:
    """Apply Kartikay-compatible deterministic policy to verified evidence."""

    def __init__(self, *, threshold_fraction: float = 0.80, review_margin: float = 0.05) -> None:
        if not 0.0 < threshold_fraction <= 1.0:
            raise ValueError("threshold_fraction must be in (0, 1]")
        if review_margin < 0.0:
            raise ValueError("review_margin must not be negative")
        self.threshold_fraction = float(threshold_fraction)
        self.review_margin = float(review_margin)

    def decide(self, evidence: Iterable[ReleaseEvidence]) -> ReleaseDecision:
        """Return a stable PASS/REVIEW/BLOCK verdict from verified failures.

        The first evidence item establishes the compared candidate and
        baseline. Every later item must use the same identities, preventing a
        release decision from mixing unrelated experiments.
        """
        items = list(evidence)
        if not items:
            return self._empty_decision()

        candidate = items[0].candidate
        baseline = items[0].baseline
        for item in items[1:]:
            if item.candidate != candidate or item.baseline != baseline:
                raise ValueError("all release evidence must use the same candidate and baseline")

        verified = [item for item in items if item.verified]
        findings = tuple(self._evaluate(item) for item in verified)
        if not findings:
            return ReleaseDecision(
                verdict=ReleaseVerdict.PASS,
                rationale="No verified failures were eligible for release evaluation.",
                evaluated_findings=0,
                verified_failures=0,
                highest_severity=None,
                triggering_failure_fingerprints=(),
                candidate=candidate,
                baseline=baseline,
                findings=(),
            )

        has_block = any(finding.internal_policy == "block" for finding in findings)
        has_review = any(finding.internal_policy == "warn" for finding in findings)
        if has_block:
            verdict = ReleaseVerdict.BLOCK
            rationale = "At least one verified regression failed outside the review margin under block policy."
        elif has_review:
            verdict = ReleaseVerdict.REVIEW
            rationale = "Verified regression evidence requires review under deterministic policy."
        else:
            verdict = ReleaseVerdict.PASS
            rationale = "All verified regression evidence met deterministic thresholds."

        triggers = tuple(
            finding.failure_fingerprint
            for finding in findings
            if map_internal_policy(finding.internal_policy) == verdict and verdict is not ReleaseVerdict.PASS
        )
        return ReleaseDecision(
            verdict=verdict,
            rationale=rationale,
            evaluated_findings=len(findings),
            verified_failures=len(verified),
            highest_severity=max(
                (item.severity for item in verified), key=lambda severity: _SEVERITY_ORDER[severity]
            ),
            triggering_failure_fingerprints=triggers,
            candidate=candidate,
            baseline=baseline,
            findings=findings,
        )

    def _evaluate(self, item: ReleaseEvidence) -> ReleaseFinding:
        minimum = item.baseline_score * self.threshold_fraction
        if item.candidate_score >= minimum:
            status = "passed"
            policy = "allow"
        elif item.candidate_score >= minimum - self.review_margin:
            status = "review_required"
            policy = "warn"
        elif item.severity in {PublicSeverity.HIGH, PublicSeverity.CRITICAL}:
            status = "failed"
            policy = "block"
        else:
            status = "failed"
            policy = "warn"
        return ReleaseFinding(
            failure_fingerprint=item.failure_fingerprint,
            severity=item.severity,
            internal_policy=policy,
            observed_score=item.candidate_score,
            minimum_threshold=minimum,
            status=status,
        )

    @staticmethod
    def _empty_decision() -> ReleaseDecision:
        unknown = ModelIdentity(model_id="", name="", version="")
        return ReleaseDecision(
            verdict=ReleaseVerdict.PASS,
            rationale="No verified failures were eligible for release evaluation.",
            evaluated_findings=0,
            verified_failures=0,
            highest_severity=None,
            triggering_failure_fingerprints=(),
            candidate=unknown,
            baseline=unknown,
            findings=(),
        )


def _identity(metadata: Any) -> ModelIdentity:
    return ModelIdentity(
        model_id=metadata.model_id,
        name=metadata.name,
        version=metadata.version,
    )
