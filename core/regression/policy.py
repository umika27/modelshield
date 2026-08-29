from __future__ import annotations

from typing import List, Tuple

from core.schemas.decision import (
    CheckStatusEnum,
    DecisionEnum,
    DecisionSummary,
    RegressionCheckResult,
    RegressionFailureItem,
)
from core.schemas.regression import PolicyEnum, RegressionRecord


class PolicyEvaluator:
    """Evaluates candidate performance against individual regression thresholds and computes aggregate release decision."""

    def evaluate_check(
        self,
        regression: RegressionRecord,
        observed_score: float,
    ) -> RegressionCheckResult:
        """Evaluate a single regression record against an observed candidate metric."""
        min_threshold = regression.metric.minimum_threshold
        review_margin = regression.metric.review_margin

        if observed_score >= min_threshold:
            status = CheckStatusEnum.PASSED
            msg = f"Observed {regression.metric.name} ({observed_score:.4f}) met threshold ({min_threshold:.4f})."
        elif observed_score >= (min_threshold - review_margin):
            status = CheckStatusEnum.REVIEW_REQUIRED
            msg = (
                f"Observed {regression.metric.name} ({observed_score:.4f}) is in review margin "
                f"[{min_threshold - review_margin:.4f}, {min_threshold:.4f}]."
            )
        else:
            status = CheckStatusEnum.FAILED
            msg = f"Observed {regression.metric.name} ({observed_score:.4f}) failed threshold ({min_threshold:.4f})."

        return RegressionCheckResult(
            regression_id=regression.regression_id,
            failure_id=regression.failure_id,
            name=regression.name,
            status=status,
            policy=regression.policy,
            observed_score=observed_score,
            minimum_threshold=min_threshold,
            metric_name=regression.metric.name,
            details={
                "condition_type": regression.condition.type,
                "parameters": regression.condition.parameters,
            },
            message=msg,
        )

    def aggregate_decision(
        self,
        results: List[RegressionCheckResult],
    ) -> Tuple[DecisionEnum, DecisionSummary, List[RegressionFailureItem], str]:
        """Compute the final release decision (PASS / REVIEW / BLOCK) from individual check results."""
        summary = DecisionSummary(total_regressions=len(results))
        failures_and_warnings: List[RegressionFailureItem] = []

        has_block_failure = False
        has_review_or_warn = False

        for r in results:
            if r.status == CheckStatusEnum.PASSED:
                summary.passed += 1
            elif r.status == CheckStatusEnum.REVIEW_REQUIRED:
                summary.review_required += 1
                has_review_or_warn = True
                failures_and_warnings.append(
                    RegressionFailureItem(
                        regression_id=r.regression_id,
                        failure_id=r.failure_id,
                        status=r.status,
                        policy=r.policy,
                        name=r.name,
                        observed_score=r.observed_score,
                        threshold=r.minimum_threshold,
                        message=r.message,
                    )
                )
            else:  # FAILED
                summary.failed += 1
                failures_and_warnings.append(
                    RegressionFailureItem(
                        regression_id=r.regression_id,
                        failure_id=r.failure_id,
                        status=r.status,
                        policy=r.policy,
                        name=r.name,
                        observed_score=r.observed_score,
                        threshold=r.minimum_threshold,
                        message=r.message,
                    )
                )
                if r.policy == PolicyEnum.BLOCK:
                    has_block_failure = True
                else:
                    has_review_or_warn = True

        # Determine aggregate verdict
        if has_block_failure:
            decision = DecisionEnum.BLOCK
            reason = f"Candidate failed {summary.failed} regression test(s) with BLOCK policy."
        elif has_review_or_warn:
            decision = DecisionEnum.REVIEW
            reason = f"Candidate requires review: {summary.review_required} review item(s), {summary.failed} warning item(s)."
        else:
            decision = DecisionEnum.PASS
            reason = f"All {summary.total_regressions} regression checks passed successfully."

        return decision, summary, failures_and_warnings, reason
