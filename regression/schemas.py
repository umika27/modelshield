"""Data schemas for ModelShield Regression Engine and Release Gating.
Conforms directly to docs/contracts/ specifications.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyEnum(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    ALLOW = "allow"


class DecisionEnum(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


class CheckStatusEnum(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


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
    """Schema matching docs/contracts/failure_record.json"""
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


class RegressionMetricThreshold(BaseModel):
    name: str
    minimum_threshold: float
    review_margin: float = 0.05


class RegressionRecord(BaseModel):
    """Schema matching docs/contracts/regression_record.json"""
    schema_version: str = "1.0"
    regression_id: str
    failure_id: str
    name: str
    condition: ConditionSpec
    metric: RegressionMetricThreshold
    policy: PolicyEnum = PolicyEnum.BLOCK
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class RegressionFailureItem(BaseModel):
    regression_id: str
    failure_id: str
    status: CheckStatusEnum
    policy: PolicyEnum
    name: Optional[str] = None
    observed_score: Optional[float] = None
    threshold: Optional[float] = None
    message: Optional[str] = None


class DecisionSummary(BaseModel):
    total_regressions: int = 0
    passed: int = 0
    failed: int = 0
    review_required: int = 0


class RegressionCheckResult(BaseModel):
    """Detailed execution result for a single regression check."""
    regression_id: str
    failure_id: str
    name: str
    status: CheckStatusEnum
    policy: PolicyEnum
    observed_score: float
    minimum_threshold: float
    metric_name: str
    details: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class ReleaseDecision(BaseModel):
    """Schema matching docs/contracts/release_decision.json"""
    schema_version: str = "1.0"
    decision_id: str
    model: ModelRef
    decision: DecisionEnum
    summary: DecisionSummary
    failures: List[RegressionFailureItem] = Field(default_factory=list)
    detailed_checks: List[RegressionCheckResult] = Field(default_factory=list)
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_contract_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "model": {
                "name": self.model.name,
                "version": self.model.version,
            },
            "decision": self.decision.value,
            "summary": {
                "total_regressions": self.summary.total_regressions,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "review_required": self.summary.review_required,
            },
            "failures": [
                {
                    "regression_id": f.regression_id,
                    "failure_id": f.failure_id,
                    "status": f.status.value,
                    "policy": f.policy.value,
                }
                for f in self.failures
            ],
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class EvaluationResult(BaseModel):
    """Schema matching docs/contracts/evaluation_result.json"""
    schema_version: str = "1.0"
    evaluation_id: str
    experiment_id: str
    model: ModelRef
    baseline: Dict[str, Any]
    candidate: Dict[str, Any]
    condition: ConditionSpec
    metric: FailureMetric
    status: str
    threshold: Dict[str, Any]
    reproducibility: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
