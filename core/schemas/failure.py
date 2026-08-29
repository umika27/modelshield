from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ModelRef(BaseModel):
    name: str
    version: str
    artifact_reference: Optional[str] = None


class ConditionSpec(BaseModel):
    type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class FailureMetric(BaseModel):
    name: str
    baseline_score: float
    candidate_score: float
    delta: float


class VerificationInfo(BaseModel):
    status: str = "verified"
    verification_runs: int = 1
    consistent: bool = True


class DatasetRef(BaseModel):
    name: str
    version: str
    reference: Optional[str] = None


class FailureRecord(BaseModel):
    schema_version: str = "1.0"
    failure_id: str
    evaluation_id: Optional[str] = None
    experiment_id: Optional[str] = None
    model: ModelRef
    condition: ConditionSpec
    metric: FailureMetric
    severity: str = "critical"  # critical, high, medium, low
    verification: VerificationInfo = Field(default_factory=VerificationInfo)
    reproducibility_capsule_id: Optional[str] = None
    dataset: Optional[DatasetRef] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
