from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.schemas.failure import ModelRef
from core.schemas.regression import PolicyEnum


class DecisionEnum(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


class CheckStatusEnum(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


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
    """Detailed result of an individual regression check execution."""
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
    """Corresponds to docs/contracts/release_decision.json."""
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
        """Convert to the exact dictionary format specified in docs/contracts/release_decision.json."""
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
