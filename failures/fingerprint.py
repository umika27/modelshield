"""
Failure Fingerprint — turns a raw EvaluationResult into a
structured FailureRecord.

Shared JSON contract (frozen, Section 12 of the playbook):

EvaluationResult:
    model, experiment_id, condition, parameters,
    baseline_score, candidate_score, delta, status, seed

FailureRecord (what we produce here):
    failure_id, condition, parameters, baseline_score,
    candidate_score, delta, severity, verified
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class EvaluationResult:
    model: str
    experiment_id: str
    condition: str
    parameters: dict[str, Any]
    baseline_score: float
    candidate_score: float
    delta: float
    status: str  # "pass" | "failure"
    seed: Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EvaluationResult":
        return cls(
            model=d["model"],
            experiment_id=d["experiment_id"],
            condition=d["condition"],
            parameters=d.get("parameters", {}),
            baseline_score=d["baseline_score"],
            candidate_score=d["candidate_score"],
            delta=d["delta"],
            status=d["status"],
            seed=d.get("seed"),
        )


@dataclass
class FailureRecord:
    condition: str
    parameters: dict[str, Any]
    baseline_score: float
    candidate_score: float
    delta: float
    severity: str  # "minor" | "major" | "critical"
    verified: bool = False
    model_id: Optional[str] = None
    dataset_ref: Optional[str] = None
    evaluation_id: Optional[int] = None
    failure_id: Optional[int] = None  # set once persisted

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- Severity classification ------------------------------------------------
#
# Kept simple and configurable per Section 10 of the playbook: never claim a
# single universal threshold for every task. These are sane MVP defaults —
# override severity_bands if your CV task needs different cut points.

DEFAULT_SEVERITY_BANDS = (
    (0.30, "critical"),   # |delta| >= 0.30
    (0.15, "major"),      # |delta| >= 0.15
    (0.0, "minor"),       # anything else that still failed
)


def classify_severity(delta: float, bands=DEFAULT_SEVERITY_BANDS) -> str:
    magnitude = abs(delta)
    for cutoff, label in bands:
        if magnitude >= cutoff:
            return label
    return "minor"


def build_fingerprint(
    result: EvaluationResult,
    *,
    model_id: Optional[str] = None,
    dataset_ref: Optional[str] = None,
    evaluation_id: Optional[int] = None,
    severity_bands=DEFAULT_SEVERITY_BANDS,
) -> FailureRecord:
    """Build an (unverified) FailureRecord from an EvaluationResult.

    Only call this when result.status == "failure" — verification and
    promotion into Failure Memory happens separately (see memory.py).
    """
    if result.status != "failure":
        raise ValueError(
            f"build_fingerprint expects a failing EvaluationResult, "
            f"got status={result.status!r} for condition={result.condition!r}"
        )

    return FailureRecord(
        condition=result.condition,
        parameters=result.parameters,
        baseline_score=result.baseline_score,
        candidate_score=result.candidate_score,
        delta=result.delta,
        severity=classify_severity(result.delta, severity_bands),
        verified=False,
        model_id=model_id or result.model,
        dataset_ref=dataset_ref,
        evaluation_id=evaluation_id,
    )
