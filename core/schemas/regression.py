from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PolicyEnum(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    ALLOW = "allow"


class RegressionCondition(BaseModel):
    type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class RegressionMetricThreshold(BaseModel):
    name: str
    minimum_threshold: float
    # Optional margin for warning/review before blocking
    review_margin: float = 0.05


class RegressionRecord(BaseModel):
    schema_version: str = "1.0"
    regression_id: str
    failure_id: str
    name: str
    condition: RegressionCondition
    metric: RegressionMetricThreshold
    policy: PolicyEnum = PolicyEnum.BLOCK
    enabled: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
