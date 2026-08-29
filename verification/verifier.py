"""Orchestration for repeatable verification of evaluation failures."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.schemas import EvaluationResult


@dataclass(frozen=True)
class VerificationResult:
    """The evidence collected while attempting to reproduce one failure."""

    original_evaluation_id: str
    experiment_id: str
    verified: bool
    runs: int
    successful_reproductions: int
    results: tuple[EvaluationResult, ...]
    reason: str
    failure_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if self.runs < 0 or self.successful_reproductions < 0:
            raise ValueError("runs and successful_reproductions must not be negative")
        if self.successful_reproductions > self.runs:
            raise ValueError("successful_reproductions cannot exceed runs")
        if len(self.results) != self.runs:
            raise ValueError("results must contain one entry per executed verification run")
        if self.verified != (self.runs > 0 and self.successful_reproductions == self.runs):
            raise ValueError("verified must agree with the reproduction evidence")

    def to_dict(self, *, include_results: bool = True) -> dict[str, Any]:
        """Return a JSON-serializable representation for downstream consumers."""
        data: dict[str, Any] = {
            "original_evaluation_id": self.original_evaluation_id,
            "experiment_id": self.experiment_id,
            "verified": self.verified,
            "runs": self.runs,
            "successful_reproductions": self.successful_reproductions,
            "reason": self.reason,
            "failure_fingerprint": self.failure_fingerprint,
        }
        if include_results:
            data["results"] = [result.to_dict() for result in self.results]
        return data


class VerificationEngine:
    """Verify failures by calling an injected repeat-evaluation callback.

    A reproduction succeeds only if it is still a failure and retains the
    original model identities, experiment, condition/parameters, metric,
    threshold comparison, and seed. Scores may vary.
    """

    def verify(
        self,
        initial_result: EvaluationResult,
        evaluate_again: Callable[[], EvaluationResult],
        *,
        runs: int = 3,
    ) -> VerificationResult:
        """Repeat a failed evaluation and return reproducibility evidence."""
        if not isinstance(initial_result, EvaluationResult):
            raise TypeError("initial_result must be an EvaluationResult")
        if isinstance(runs, bool) or not isinstance(runs, int) or runs <= 0:
            raise ValueError("runs must be a positive integer")
        if not callable(evaluate_again):
            raise TypeError("evaluate_again must be callable")
        if initial_result.status != "failure":
            return VerificationResult(
                original_evaluation_id=initial_result.evaluation_id,
                experiment_id=initial_result.experiment_id,
                verified=False,
                runs=0,
                successful_reproductions=0,
                results=(),
                reason="Original evaluation is not a failure; verification was not required.",
            )

        repeated_results: list[EvaluationResult] = []
        successes = 0
        for _ in range(runs):
            repeated = evaluate_again()
            if not isinstance(repeated, EvaluationResult):
                raise TypeError("evaluate_again must return an EvaluationResult")
            repeated_results.append(repeated)
            if self._is_reproduction(initial_result, repeated):
                successes += 1

        verified = successes == runs
        reason = (
            "Failure reproduced in all verification runs."
            if verified
            else f"Failure did not reproduce consistently: {successes}/{runs} runs matched the original failure configuration."
        )
        fingerprint = None
        if verified:
            # Local import avoids coupling verification orchestration to hash implementation.
            from .fingerprint import FailureFingerprinter

            fingerprint = FailureFingerprinter().generate(initial_result)
        return VerificationResult(
            original_evaluation_id=initial_result.evaluation_id,
            experiment_id=initial_result.experiment_id,
            verified=verified,
            runs=runs,
            successful_reproductions=successes,
            results=tuple(repeated_results),
            reason=reason,
            failure_fingerprint=fingerprint,
        )

    @staticmethod
    def _is_reproduction(original: EvaluationResult, repeated: EvaluationResult) -> bool:
        return (
            repeated.status == "failure"
            and repeated.experiment_id == original.experiment_id
            and VerificationEngine._model_identity(repeated.model) == VerificationEngine._model_identity(original.model)
            and VerificationEngine._model_identity(repeated.baseline) == VerificationEngine._model_identity(original.baseline)
            and VerificationEngine._model_identity(repeated.candidate) == VerificationEngine._model_identity(original.candidate)
            and repeated.challenge.type == original.challenge.type
            and repeated.challenge.parameters == original.challenge.parameters
            and repeated.seed == original.seed
            and repeated.metric_name == original.metric_name
            and repeated.threshold == original.threshold
            and repeated.threshold_comparison == original.threshold_comparison
        )

    @staticmethod
    def _model_identity(model: Any) -> tuple[str, str]:
        return model.name, model.version
