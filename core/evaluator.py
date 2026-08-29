"""Deterministic baseline-vs-candidate evaluation orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

import torch
from torch import Tensor, nn

from .metrics import classification_accuracy
from .runner import ModelRunner
from .schemas import ChallengeSpec, EvaluationResult, ExperimentMetadata, ModelMetadata

ChallengeTransform = Callable[[Tensor, ChallengeSpec], Tensor]


class EvaluationEngine:
    """Compare two models using equal values from one challenge application."""

    def __init__(self, runner: ModelRunner | None = None) -> None:
        self.runner = runner or ModelRunner()

    def evaluate(
        self,
        *,
        baseline_model: nn.Module,
        candidate_model: nn.Module,
        inputs: Tensor,
        labels: Tensor,
        baseline_metadata: ModelMetadata,
        candidate_metadata: ModelMetadata,
        experiment: ExperimentMetadata,
        challenge: ChallengeSpec,
        evaluation_id: str,
        challenge_transform: ChallengeTransform | None = None,
        timestamp: datetime | None = None,
    ) -> EvaluationResult:
        """Evaluate both models against the same challenged input values.

        ``challenge_transform`` is injected in Phase 1. Future challenge modules
        will implement it; it is deliberately called exactly once per evaluation.
        """
        if not isinstance(inputs, Tensor) or not isinstance(labels, Tensor):
            raise TypeError("inputs and labels must be torch.Tensor instances")
        if inputs.ndim == 0 or labels.ndim != 1 or inputs.shape[0] != labels.shape[0]:
            raise ValueError("inputs and one-dimensional labels must share batch length")
        if baseline_metadata.model_id != experiment.baseline_model_id:
            raise ValueError("baseline metadata does not match experiment metadata")
        if candidate_metadata.model_id != experiment.candidate_model_id:
            raise ValueError("candidate metadata does not match experiment metadata")

        source_copy = inputs.detach().clone()
        if challenge_transform is None:
            challenged = source_copy
        elif challenge.reproducible:
            # Scope the seed so repeated evaluations are reproducible without
            # unexpectedly changing the caller's global PyTorch RNG state.
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(challenge.seed)
                challenged = challenge_transform(source_copy, challenge)
        else:
            challenged = challenge_transform(source_copy, challenge)
        if not isinstance(challenged, Tensor):
            raise TypeError("challenge_transform must return a torch.Tensor")
        if challenged.shape[0] != labels.shape[0]:
            raise ValueError("challenged inputs must retain the batch dimension")

        # Separate clones protect equality of values if a poorly behaved model mutates input.
        baseline_predictions = self.runner.predict(baseline_model, challenged.detach().clone())
        candidate_predictions = self.runner.predict(candidate_model, challenged.detach().clone())
        baseline_score = classification_accuracy(baseline_predictions, labels)
        candidate_score = classification_accuracy(candidate_predictions, labels)
        delta = candidate_score - baseline_score
        status = "failure" if delta <= experiment.threshold else "pass"

        return EvaluationResult(
            evaluation_id=evaluation_id,
            experiment_id=experiment.experiment_id,
            model=candidate_metadata,
            baseline=baseline_metadata,
            candidate=candidate_metadata,
            challenge=challenge,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
            threshold=experiment.threshold,
            status=status,
            seed=challenge.seed,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
