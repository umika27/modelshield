from __future__ import annotations

from typing import Optional

from core.schemas.failure import FailureRecord
from core.schemas.regression import (
    PolicyEnum,
    RegressionCondition,
    RegressionMetricThreshold,
    RegressionRecord,
)


class FailureToRegressionCompiler:
    """Compiles verified FailureRecords into active RegressionRecords (The REMEMBER phase)."""

    def __init__(self, default_tolerance_ratio: float = 0.80, default_review_margin: float = 0.05):
        """
        Args:
            default_tolerance_ratio: Proportion of baseline score to require (e.g. 0.80 means >= 80% of baseline).
            default_review_margin: Buffer below threshold that triggers a REVIEW before a hard block.
        """
        self.default_tolerance_ratio = default_tolerance_ratio
        self.default_review_margin = default_review_margin

    def compile(
        self,
        failure: FailureRecord,
        custom_threshold: Optional[float] = None,
        custom_policy: Optional[PolicyEnum] = None,
        custom_name: Optional[str] = None,
    ) -> RegressionRecord:
        """Transform a FailureRecord into a RegressionRecord."""
        # Calculate minimum threshold
        if custom_threshold is not None:
            min_threshold = custom_threshold
        else:
            baseline = failure.metric.baseline_score
            # Default minimum threshold e.g. 80% of baseline score
            min_threshold = round(baseline * self.default_tolerance_ratio, 4)

        # Determine policy from severity or override
        if custom_policy is not None:
            policy = custom_policy
        elif failure.severity.lower() in ("critical", "high"):
            policy = PolicyEnum.BLOCK
        else:
            policy = PolicyEnum.WARN

        # Generate human-readable name
        if custom_name:
            name = custom_name
        else:
            cond_title = failure.condition.type.replace("_", " ").title()
            name = f"{cond_title} regression"

        # Construct regression ID
        reg_id = (
            failure.failure_id.replace("failure-", "regression-")
            if failure.failure_id.startswith("failure-")
            else f"regression-{failure.failure_id}"
        )

        return RegressionRecord(
            schema_version=failure.schema_version,
            regression_id=reg_id,
            failure_id=failure.failure_id,
            name=name,
            condition=RegressionCondition(
                type=failure.condition.type,
                parameters=failure.condition.parameters,
            ),
            metric=RegressionMetricThreshold(
                name=failure.metric.name,
                minimum_threshold=min_threshold,
                review_margin=self.default_review_margin,
            ),
            policy=policy,
            enabled=True,
        )
