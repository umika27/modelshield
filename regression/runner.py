"""Regression Runner for ModelShield.
Executes regression tests, checks thresholds, loads failure memories, and gates releases.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

from regression.adapter import EvaluationIntegrationError, EvaluatorProtocol
from regression.policy import PolicyEvaluator
from regression.schemas import (
    DecisionEnum,
    FailureRecord,
    ModelRef,
    PolicyEnum,
    RegressionCheckResult,
    RegressionMetricThreshold,
    RegressionRecord,
    ReleaseDecision,
)


class RegressionRunner:
    """Runner for executing regression suites, compiling failure memories, and gating model releases."""

    def __init__(
        self,
        failures_path: Optional[Union[str, Path]] = None,
        regressions_path: Optional[Union[str, Path]] = None,
        policy_evaluator: Optional[PolicyEvaluator] = None,
        evaluator: Optional[Union[EvaluatorProtocol, Callable[[ModelRef, str, Dict[str, Any], str], float]]] = None,
    ):
        self.failures_path = Path(failures_path) if failures_path else None
        self.regressions_path = Path(regressions_path) if regressions_path else None
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()
        self._custom_evaluator: Optional[Union[EvaluatorProtocol, Callable[[ModelRef, str, Dict[str, Any], str], float]]] = evaluator

    def set_evaluator(
        self,
        eval_fn: Union[EvaluatorProtocol, Callable[[ModelRef, str, Dict[str, Any], str], float]],
    ) -> None:
        """Register an evaluator instance or function (e.g. ChallengeEvaluationAdapter)."""
        self._custom_evaluator = eval_fn

    # -------------------------------------------------------------------------
    # Failure Memory Operations
    # -------------------------------------------------------------------------

    def load_failures(self, path: Optional[Union[str, Path]] = None) -> List[FailureRecord]:
        """Load failure records from a file (single record or array) or directory of JSONs."""
        target_path = Path(path) if path else self.failures_path
        if not target_path or not target_path.exists():
            return []

        failures: List[FailureRecord] = []
        if target_path.is_file():
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    failures.extend([FailureRecord.model_validate(item) for item in data])
                else:
                    failures.append(FailureRecord.model_validate(data))
        elif target_path.is_dir():
            for p in sorted(target_path.glob("*.json")):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            failures.extend([FailureRecord.model_validate(item) for item in data])
                        else:
                            failures.append(FailureRecord.model_validate(data))
                except Exception:
                    continue
        return failures

    def compile_failure_to_regression(
        self,
        failure: FailureRecord,
        minimum_threshold: Optional[float] = None,
        policy: Optional[PolicyEnum] = None,
    ) -> RegressionRecord:
        """Turn a verified FailureRecord into a RegressionRecord (REMEMBER stage)."""
        min_thresh = (
            minimum_threshold
            if minimum_threshold is not None
            else round(failure.metric.baseline_score * 0.80, 4)
        )
        pol = policy or (PolicyEnum.BLOCK if failure.severity.lower() in ("critical", "high") else PolicyEnum.WARN)
        reg_id = (
            failure.failure_id.replace("failure-", "regression-")
            if failure.failure_id.startswith("failure-")
            else f"regression-{failure.failure_id}"
        )
        name = f"{failure.condition.type.replace('_', ' ').title()} regression"

        return RegressionRecord(
            schema_version="1.0",
            regression_id=reg_id,
            failure_id=failure.failure_id,
            name=name,
            condition=failure.condition,
            metric=RegressionMetricThreshold(
                name=failure.metric.name,
                minimum_threshold=min_thresh,
                review_margin=0.05,
            ),
            policy=pol,
            enabled=True,
        )

    # -------------------------------------------------------------------------
    # Regression Suite Operations
    # -------------------------------------------------------------------------

    def load_regressions(self, path: Optional[Union[str, Path]] = None) -> List[RegressionRecord]:
        """Load regression records from file, directory, or compiled from failure store."""
        target_path = Path(path) if path else self.regressions_path
        if not target_path or not target_path.exists():
            # If no regressions directory exists, compile from failures
            failures = self.load_failures()
            return [self.compile_failure_to_regression(f) for f in failures if f.verification.status.lower() == "verified"]

        regressions: List[RegressionRecord] = []
        if target_path.is_file():
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    regressions.extend([RegressionRecord.model_validate(item) for item in data])
                else:
                    regressions.append(RegressionRecord.model_validate(data))
        elif target_path.is_dir():
            for p in sorted(target_path.glob("*.json")):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            regressions.extend([RegressionRecord.model_validate(item) for item in data])
                        else:
                            regressions.append(RegressionRecord.model_validate(data))
                except Exception:
                    continue
        return regressions

    # -------------------------------------------------------------------------
    # Execution & Gating
    # -------------------------------------------------------------------------

    def run_regression_suite(
        self,
        candidate_model: ModelRef,
        regressions: Optional[List[RegressionRecord]] = None,
        score_overrides: Optional[Dict[str, float]] = None,
        decision_id: Optional[str] = None,
    ) -> ReleaseDecision:
        """Run all active regression tests on candidate model and emit a ReleaseDecision."""
        suite = regressions if regressions is not None else self.load_regressions()
        enabled_tests = [r for r in suite if r.enabled]
        score_overrides = score_overrides or {}

        check_results: List[RegressionCheckResult] = []
        for reg in enabled_tests:
            # Determine observed score
            if reg.regression_id in score_overrides:
                observed_score = score_overrides[reg.regression_id]
            elif self._custom_evaluator is not None:
                if hasattr(self._custom_evaluator, "evaluate_condition"):
                    observed_score = self._custom_evaluator.evaluate_condition(
                        candidate_model=candidate_model,
                        condition_type=reg.condition.type,
                        parameters=reg.condition.parameters,
                        metric_name=reg.metric.name,
                    )
                else:
                    observed_score = self._custom_evaluator(
                        candidate_model,
                        reg.condition.type,
                        reg.condition.parameters,
                        reg.metric.name,
                    )
            else:
                raise EvaluationIntegrationError(
                    f"No evaluation adapter or custom evaluator registered to execute regression check "
                    f"'{reg.regression_id}' on candidate '{candidate_model.name}:{candidate_model.version}'. "
                    f"Register an evaluation adapter via runner.set_evaluator(adapter)."
                )

            result = self.policy_evaluator.evaluate_check(
                regression=reg,
                observed_score=observed_score,
            )
            check_results.append(result)

        decision, summary, flagged_items, reason = self.policy_evaluator.aggregate_decision(check_results)

        return ReleaseDecision(
            decision_id=decision_id or f"decision-{uuid.uuid4().hex[:6]}",
            model=candidate_model,
            decision=decision,
            summary=summary,
            failures=flagged_items,
            detailed_checks=check_results,
            reason=reason,
        )

    def replay_failure(
        self,
        failure_id: str,
        candidate_model: ModelRef,
        failures_path: Optional[Union[str, Path]] = None,
    ) -> RegressionCheckResult:
        """Replay a specific verified failure condition against a candidate model."""
        failures = self.load_failures(failures_path)
        matching = [f for f in failures if f.failure_id == failure_id]
        if not matching:
            raise ValueError(f"FailureRecord with ID '{failure_id}' not found.")

        target_failure = matching[0]
        regression = self.compile_failure_to_regression(target_failure)

        if self._custom_evaluator:
            if hasattr(self._custom_evaluator, "evaluate_condition"):
                score = self._custom_evaluator.evaluate_condition(
                    candidate_model=candidate_model,
                    condition_type=regression.condition.type,
                    parameters=regression.condition.parameters,
                    metric_name=regression.metric.name,
                )
            else:
                score = self._custom_evaluator(
                    candidate_model,
                    regression.condition.type,
                    regression.condition.parameters,
                    regression.metric.name,
                )
        else:
            score = target_failure.metric.candidate_score

        return self.policy_evaluator.evaluate_check(regression, score)
