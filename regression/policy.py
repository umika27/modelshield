"""Policy evaluator for ModelShield Regression Engine.
Enforces release gates, minimum score thresholds, review margins, and severity rules.
"""
from __future__ import annotations

from typing import List, Tuple

from regression.schemas import (
    CheckStatusEnum,
    DecisionEnum,
    DecisionSummary,
    PolicyEnum,
    RegressionCheckResult,
    RegressionFailureItem,
    RegressionRecord,
)


class PolicyEvaluator:
    """Evaluates candidate performance against regression contracts and computes release verdicts."""

    def evaluate_check(
        self,
        regression: RegressionRecord,
        observed_score: float,
    ) -> RegressionCheckResult:
        """Evaluate a candidate model's observed metric against a specific regression requirement."""
        min_threshold = regression.metric.minimum_threshold
        review_margin = regression.metric.review_margin

        if observed_score >= min_threshold:
            status = CheckStatusEnum.PASSED
            msg = f"Passed: observed {regression.metric.name} ({observed_score:.4f}) >= threshold ({min_threshold:.4f})."
        elif observed_score >= (min_threshold - review_margin):
            status = CheckStatusEnum.REVIEW_REQUIRED
            msg = (
                f"Review required: observed {regression.metric.name} ({observed_score:.4f}) is within margin "
                f"[{min_threshold - review_margin:.4f}, {min_threshold:.4f}]."
            )
        else:
            status = CheckStatusEnum.FAILED
            msg = f"Failed: observed {regression.metric.name} ({observed_score:.4f}) < threshold ({min_threshold:.4f})."

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
        """Aggregate multiple check results into a release gating decision: PASS, REVIEW, or BLOCK."""
        summary = DecisionSummary(total_regressions=len(results))
        flagged_items: List[RegressionFailureItem] = []

        has_block_failure = False
        has_review_or_warn = False

        for r in results:
            if r.status == CheckStatusEnum.PASSED:
                summary.passed += 1
            elif r.status == CheckStatusEnum.REVIEW_REQUIRED:
                summary.review_required += 1
                has_review_or_warn = True
                flagged_items.append(
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
                flagged_items.append(
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

        if has_block_failure:
            decision = DecisionEnum.BLOCK
            reason = f"Release BLOCKED: Candidate failed {summary.failed} regression test(s) with policy 'block'."
        elif has_review_or_warn:
            decision = DecisionEnum.REVIEW
            reason = f"Release REVIEW REQUIRED: {summary.review_required} check(s) in review margin, {summary.failed} warning(s)."
        else:
            decision = DecisionEnum.PASS
            reason = f"Release PASSED: All {summary.total_regressions} regression checks satisfied thresholds."

        return decision, summary, flagged_items, reason
