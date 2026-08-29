"""Evaluation adapter for ModelShield Regression Engine.
Bridges candidate model inference, challenge transforms, and metric evaluation.
"""
from __future__ import annotations

import random
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from regression.schemas import FailureRecord, ModelRef


class EvaluationIntegrationError(Exception):
    """Raised when required ML evaluation components (model loader, challenge runner, metric evaluator)
    are not registered or fail to evaluate a condition.
    """
    pass


@runtime_checkable
class EvaluatorProtocol(Protocol):
    """Protocol for model evaluation under a challenge condition."""

    def evaluate_condition(
        self,
        candidate_model: ModelRef,
        condition_type: str,
        parameters: Dict[str, Any],
        metric_name: str,
        seed: Optional[int] = None,
    ) -> float:
        ...


class ChallengeEvaluationAdapter:
    """Production evaluation adapter.
    Delegates to registered model loader, challenge transform, and metric calculation handlers.
    Does not duplicate ML code and strictly requires backends for live evaluation.
    """

    def __init__(
        self,
        model_loader: Optional[Callable[[ModelRef], Any]] = None,
        challenge_runner: Optional[Callable[[Any, str, Dict[str, Any], Optional[int]], Any]] = None,
        metric_evaluator: Optional[Callable[[Any, str], float]] = None,
    ):
        self.model_loader = model_loader
        self.challenge_runner = challenge_runner
        self.metric_evaluator = metric_evaluator

    def register_backend(
        self,
        model_loader: Callable[[ModelRef], Any],
        challenge_runner: Callable[[Any, str, Dict[str, Any], Optional[int]], Any],
        metric_evaluator: Callable[[Any, str], float],
    ) -> None:
        """Register the live ML pipeline handlers."""
        self.model_loader = model_loader
        self.challenge_runner = challenge_runner
        self.metric_evaluator = metric_evaluator

    def evaluate_condition(
        self,
        candidate_model: ModelRef,
        condition_type: str,
        parameters: Dict[str, Any],
        metric_name: str,
        seed: Optional[int] = None,
    ) -> float:
        """Execute candidate model evaluation under stored challenge condition and return observed metric score."""
        if not self.model_loader:
            raise EvaluationIntegrationError(
                f"No model loader registered to resolve candidate model '{candidate_model.name}:{candidate_model.version}'."
            )
        if not self.challenge_runner:
            raise EvaluationIntegrationError(
                f"No challenge runner registered to execute condition '{condition_type}'."
            )
        if not self.metric_evaluator:
            raise EvaluationIntegrationError(
                f"No metric evaluator registered to calculate metric '{metric_name}'."
            )

        # 1. Resolve/load model
        model = self.model_loader(candidate_model)

        # 2. Extract seed from parameters or argument for deterministic reproducibility
        effective_seed = seed if seed is not None else parameters.get("seed", 42)

        # 3. Execute challenge transform and candidate model inference
        raw_outputs = self.challenge_runner(model, condition_type, parameters, effective_seed)

        # 4. Calculate requested metric
        score = self.metric_evaluator(raw_outputs, metric_name)

        return float(score)


class DemoTestEvaluator:
    """Explicit deterministic evaluation adapter for CLI demos and unit/integration testing.
    Calculates reproducible scores based on model version, condition severity, and seed.
    """

    def __init__(self, score_mapping: Optional[Dict[str, float]] = None):
        self.score_mapping = score_mapping or {}

    def set_score(self, condition_type: str, score: float) -> None:
        self.score_mapping[condition_type] = score

    def evaluate_condition(
        self,
        candidate_model: ModelRef,
        condition_type: str,
        parameters: Dict[str, Any],
        metric_name: str,
        seed: Optional[int] = None,
    ) -> float:
        if condition_type in self.score_mapping:
            return self.score_mapping[condition_type]

        # Deterministic score calculation respecting seed and condition parameters
        rng_seed = seed if seed is not None else parameters.get("seed", 42)
        rng = random.Random(rng_seed)

        # Base score by candidate version
        base = 0.85 if "v4" in candidate_model.version else (0.75 if "v3" in candidate_model.version else 0.50)

        # Apply degradation based on parameters
        if "brightness" in parameters and parameters["brightness"] < 0.5:
            base -= 0.25
        if "blur" in parameters and parameters["blur"] > 0.5:
            base -= 0.10
        if "contrast_factor" in parameters and parameters["contrast_factor"] < 0.5:
            base -= 0.15

        return max(0.0, min(1.0, round(base, 4)))
