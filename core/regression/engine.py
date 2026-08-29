from __future__ import annotations

import uuid
from typing import Callable, Dict, List, Optional, Union

from core.regression.compiler import FailureToRegressionCompiler
from core.regression.interfaces import (
    EvaluatorInterface,
    FailureStoreInterface,
    RegressionStoreInterface,
)
from core.regression.policy import PolicyEvaluator
from core.regression.stores import InMemoryFailureStore, InMemoryRegressionStore
from core.schemas.decision import (
    CheckStatusEnum,
    DecisionEnum,
    RegressionCheckResult,
    ReleaseDecision,
)
from core.schemas.failure import FailureRecord, ModelRef
from core.schemas.regression import PolicyEnum, RegressionRecord


class CallableEvaluator(EvaluatorInterface):
    """Adapter allowing a simple Python function to act as an EvaluatorInterface."""

    def __init__(
        self,
        eval_fn: Callable[[ModelRef, str, Dict[str, any], str], float],
    ):
        self._eval_fn = eval_fn

    def evaluate_condition(
        self,
        candidate_model: ModelRef,
        condition_type: str,
        parameters: Dict[str, any],
        metric_name: str,
    ) -> float:
        return self._eval_fn(candidate_model, condition_type, parameters, metric_name)


class RegressionEngine:
    """Core ModelShield Regression & Release Protection Engine.
    Executes the REMEMBER -> PROTECT stages of the ModelShield verification loop.
    """

    def __init__(
        self,
        failure_store: Optional[FailureStoreInterface] = None,
        regression_store: Optional[RegressionStoreInterface] = None,
        evaluator: Optional[EvaluatorInterface] = None,
        compiler: Optional[FailureToRegressionCompiler] = None,
        policy_evaluator: Optional[PolicyEvaluator] = None,
    ):
        self.failure_store = failure_store or InMemoryFailureStore()
        self.regression_store = regression_store or InMemoryRegressionStore()
        self.evaluator = evaluator
        self.compiler = compiler or FailureToRegressionCompiler()
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()

    def set_evaluator(self, evaluator: EvaluatorInterface) -> None:
        """Connect an external ML/challenge evaluation backend."""
        self.evaluator = evaluator

    def remember_failure(
        self,
        failure: Union[FailureRecord, Dict[str, any]],
        custom_threshold: Optional[float] = None,
        custom_policy: Optional[PolicyEnum] = None,
        custom_name: Optional[str] = None,
        auto_persist: bool = True,
    ) -> RegressionRecord:
        """Convert a FailureRecord into a RegressionRecord and optionally persist it (The REMEMBER phase)."""
        if isinstance(failure, dict):
            failure = FailureRecord.model_validate(failure)

        regression = self.compiler.compile(
            failure=failure,
            custom_threshold=custom_threshold,
            custom_policy=custom_policy,
            custom_name=custom_name,
        )

        if auto_persist:
            self.regression_store.save_regression(regression)

        return regression

    def remember_stored_failures(self, verified_only: bool = True) -> List[RegressionRecord]:
        """Load all failures from the failure store and compile them into active regressions."""
        stored_failures = self.failure_store.list_failures(verified_only=verified_only)
        created_regressions: List[RegressionRecord] = []
        for failure in stored_failures:
            reg = self.remember_failure(failure, auto_persist=True)
            created_regressions.append(reg)
        return created_regressions

    def run_check(
        self,
        candidate_model: ModelRef,
        regression: RegressionRecord,
        observed_score_override: Optional[float] = None,
    ) -> RegressionCheckResult:
        """Run a single regression check against the candidate model."""
        if observed_score_override is not None:
            observed_score = observed_score_override
        elif self.evaluator is not None:
            observed_score = self.evaluator.evaluate_condition(
                candidate_model=candidate_model,
                condition_type=regression.condition.type,
                parameters=regression.condition.parameters,
                metric_name=regression.metric.name,
            )
        else:
            raise ValueError(
                f"No evaluator connected to RegressionEngine and no score override provided for check '{regression.regression_id}'."
            )

        return self.policy_evaluator.evaluate_check(
            regression=regression,
            observed_score=observed_score,
        )

    def evaluate_model(
        self,
        candidate_model: Union[ModelRef, Dict[str, any]],
        regressions: Optional[List[RegressionRecord]] = None,
        score_overrides: Optional[Dict[str, float]] = None,
        decision_id: Optional[str] = None,
    ) -> ReleaseDecision:
        """Execute all active regression tests on a candidate model and generate a ReleaseDecision.
        
        Args:
            candidate_model: Candidate model reference.
            regressions: Optional list of regression records. If None, loaded from regression_store.
            score_overrides: Optional mapping of regression_id -> observed score (useful for testing or direct metrics).
            decision_id: Optional custom decision identifier.
        """
        if isinstance(candidate_model, dict):
            candidate_model = ModelRef.model_validate(candidate_model)

        suite = regressions if regressions is not None else self.regression_store.list_regressions(enabled_only=True)
        score_overrides = score_overrides or {}

        check_results: List[RegressionCheckResult] = []
        for reg in suite:
            override = score_overrides.get(reg.regression_id)
            result = self.run_check(
                candidate_model=candidate_model,
                regression=reg,
                observed_score_override=override,
            )
            check_results.append(result)

        decision, summary, failures, reason = self.policy_evaluator.aggregate_decision(check_results)

        return ReleaseDecision(
            decision_id=decision_id or f"decision-{uuid.uuid4().hex[:6]}",
            model=candidate_model,
            decision=decision,
            summary=summary,
            failures=failures,
            detailed_checks=check_results,
            reason=reason,
        )

    def evaluate_failures_directly(
        self,
        candidate_model: Union[ModelRef, Dict[str, any]],
        failures: List[Union[FailureRecord, Dict[str, any]]],
        score_overrides: Optional[Dict[str, float]] = None,
    ) -> ReleaseDecision:
        """Convenience method: takes FailureRecords, compiles them to regressions, and evaluates candidate model."""
        compiled_regressions = [
            self.remember_failure(f, auto_persist=False)
            for f in failures
        ]
        return self.evaluate_model(
            candidate_model=candidate_model,
            regressions=compiled_regressions,
            score_overrides=score_overrides,
        )
