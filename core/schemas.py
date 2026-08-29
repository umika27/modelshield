"""Typed representations of ModelShield's shared evaluation contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Mapping


def _utc_timestamp(value: datetime) -> str:
    """Return an ISO-8601 UTC timestamp matching the contract convention."""
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_mapping(value: Mapping[str, Any], field_name: str) -> dict[str, Any]:
    """Copy and validate JSON-compatible mapping data at the contract boundary."""
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    try:
        return json.loads(json.dumps(dict(value), sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{field_name} must be JSON-serializable") from exc


@dataclass(frozen=True)
class ModelMetadata:
    """Metadata supplied with a baseline or candidate model."""

    model_id: str
    name: str
    version: str
    role: str
    framework: str = "pytorch"
    task: str = "image_classification"
    artifact_reference: str = ""
    preprocessing_version: str = ""
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        for field_name in ("model_id", "name", "version", "role"):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")
        if self.role not in {"baseline", "candidate"}:
            raise ValueError("role must be either 'baseline' or 'candidate'")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "role": self.role,
            "framework": self.framework,
            "task": self.task,
            "artifact_reference": self.artifact_reference,
            "preprocessing_version": self.preprocessing_version,
        }
        if self.created_at is not None:
            data["created_at"] = _utc_timestamp(self.created_at)
        return data


@dataclass(frozen=True)
class ExperimentMetadata:
    """Evaluation configuration supplied by the experiment contract."""

    experiment_id: str
    baseline_model_id: str
    candidate_model_id: str
    dataset_name: str
    dataset_version: str
    metric_name: str = "accuracy"
    threshold: float = -0.15
    seed: int = 42
    batch_size: int = 32
    schema_version: str = "1.0"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id must not be empty")
        if not self.baseline_model_id or not self.candidate_model_id:
            raise ValueError("baseline_model_id and candidate_model_id must not be empty")
        if self.metric_name != "accuracy":
            raise ValueError("Phase 1 supports only the 'accuracy' metric")
        threshold = float(self.threshold)
        if not -1.0 <= threshold <= 0.0:
            raise ValueError("threshold must be between -1.0 and 0.0")
        object.__setattr__(self, "threshold", threshold)
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "baseline_model_id": self.baseline_model_id,
            "candidate_model_id": self.candidate_model_id,
            "dataset": {"name": self.dataset_name, "version": self.dataset_version},
            "evaluation": {"metric": self.metric_name, "threshold": self.threshold},
            "seed": self.seed,
            "configuration": {"batch_size": self.batch_size},
        }
        if self.created_at is not None:
            data["created_at"] = _utc_timestamp(self.created_at)
        return data


@dataclass(frozen=True)
class ChallengeSpec:
    """A reproducible condition description; transform implementation comes later."""

    challenge_id: str
    type: str
    parameters: Mapping[str, Any]
    parent_challenge_id: str | None = None
    source: str = "initial_suite"
    reason: str = "initial_evaluation"
    reproducible: bool = True
    seed: int = 42
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.challenge_id or not self.type:
            raise ValueError("challenge_id and type must not be empty")
        object.__setattr__(self, "parameters", _json_mapping(self.parameters, "parameters"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "challenge_id": self.challenge_id,
            "type": self.type,
            "parameters": self.parameters,
            "parent_challenge_id": self.parent_challenge_id,
            "source": self.source,
            "reason": self.reason,
            "reproducible": self.reproducible,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class EvaluationResult:
    """The exact shared EvaluationResult JSON contract produced by Core ML."""

    evaluation_id: str
    experiment_id: str
    model: ModelMetadata
    baseline: ModelMetadata
    candidate: ModelMetadata
    challenge: ChallengeSpec
    baseline_score: float
    candidate_score: float
    threshold: float
    status: str
    seed: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = "1.0"
    threshold_comparison: str = "less_than_or_equal"
    metric_name: str = "accuracy"

    def __post_init__(self) -> None:
        if not self.evaluation_id or not self.experiment_id:
            raise ValueError("evaluation_id and experiment_id must not be empty")
        if self.model.role != "candidate" or self.candidate.role != "candidate":
            raise ValueError("model and candidate metadata must have role 'candidate'")
        if self.baseline.role != "baseline":
            raise ValueError("baseline metadata must have role 'baseline'")
        if self.status not in {"pass", "failure"}:
            raise ValueError("status must be either 'pass' or 'failure'")
        if self.metric_name != "accuracy":
            raise ValueError("Phase 1 supports only the 'accuracy' metric")
        baseline_score = float(self.baseline_score)
        candidate_score = float(self.candidate_score)
        threshold = float(self.threshold)
        for name, score in (("baseline_score", baseline_score), ("candidate_score", candidate_score)):
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        object.__setattr__(self, "baseline_score", baseline_score)
        object.__setattr__(self, "candidate_score", candidate_score)
        object.__setattr__(self, "threshold", threshold)
        expected_status = "failure" if self.delta <= self.threshold else "pass"
        if self.status != expected_status:
            raise ValueError("status must agree with delta and threshold")

    @property
    def delta(self) -> float:
        return float(self.candidate_score) - float(self.baseline_score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evaluation_id": self.evaluation_id,
            "experiment_id": self.experiment_id,
            "model": {"name": self.model.name, "version": self.model.version},
            "baseline": {
                "name": self.baseline.name,
                "version": self.baseline.version,
                "score": float(self.baseline_score),
            },
            "candidate": {
                "name": self.candidate.name,
                "version": self.candidate.version,
                "score": float(self.candidate_score),
            },
            "condition": {"type": self.challenge.type, "parameters": self.challenge.parameters},
            "metric": {
                "name": self.metric_name,
                "baseline_score": float(self.baseline_score),
                "candidate_score": float(self.candidate_score),
                "delta": self.delta,
            },
            "status": self.status,
            "threshold": {
                "value": float(self.threshold),
                "comparison": self.threshold_comparison,
            },
            "reproducibility": {"seed": self.seed},
            "timestamp": _utc_timestamp(self.timestamp),
        }

    def to_json(self) -> str:
        """Serialize with stable key ordering for machine-readable output."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
