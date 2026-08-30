"""Dataset-level real baseline/candidate execution using existing components."""

from __future__ import annotations

from collections.abc import Callable

import torch
from torch import Tensor

from challenges import BlurChallenge, BrightnessChallenge, LowLightBlurChallenge, LowLightChallenge, NoiseChallenge, RotationChallenge
from core.runner import ModelRunner
from core.schemas import ChallengeSpec, EvaluationResult
from dataset_adapters import DatasetAdapter, validate_canonical_batch
from model_adapters import ModelAdapter, validate_model_dataset_compatibility

from .config import ClassSpace, ExperimentConfig
from .exceptions import ExperimentCompatibilityError, ExperimentExecutionError
from .result import ComparisonExperimentResult


class ComparisonExperimentRunner:
    """Run one real, deterministic dataset comparison without duplicating core logic."""

    _CHALLENGES: dict[str, Callable[[], object]] = {
        "blur": BlurChallenge,
        "noise": NoiseChallenge,
        "brightness": BrightnessChallenge,
        "rotation": RotationChallenge,
        "low_light": LowLightChallenge,
        "low_light_blur": LowLightBlurChallenge,
    }

    def __init__(self, config: ExperimentConfig, model_runner: ModelRunner | None = None) -> None:
        self.config = config
        self.model_runner = model_runner or ModelRunner()

    def run(
        self,
        *,
        baseline_adapter: ModelAdapter,
        candidate_adapter: ModelAdapter,
        dataset_adapter: DatasetAdapter,
        challenge_spec: ChallengeSpec,
    ) -> ComparisonExperimentResult:
        """Evaluate models on identical challenged canonical images and labels."""
        dataset_adapter.load()
        self._validate_compatibility(baseline_adapter, candidate_adapter, dataset_adapter)
        class_space = ClassSpace(dataset_adapter.metadata.class_names)
        baseline_model, candidate_model = baseline_adapter.load(), candidate_adapter.load()
        challenge = self._challenge_for(challenge_spec)
        baseline_correct = candidate_correct = total = 0
        sample_indices: list[int] = []
        loader = dataset_adapter.create_dataloader(batch_size=self.config.batch_size, shuffle=False, num_workers=0, seed=self.config.seed)
        for images, labels in loader:
            if self.config.max_samples is not None:
                remaining = self.config.max_samples - total
                if remaining <= 0:
                    break
                images, labels = images[:remaining], labels[:remaining]
            validate_canonical_batch(images)
            if labels.ndim != 1 or labels.shape[0] != images.shape[0]:
                raise ExperimentExecutionError("labels must align with the canonical image batch")
            challenged = images.detach().clone() if challenge is None else challenge.apply(images, challenge_spec.parameters, challenge_spec.seed)
            if challenged.shape != images.shape:
                raise ExperimentExecutionError("challenge must preserve canonical batch shape")
            baseline_predictions = self.model_runner.predict(baseline_model, baseline_adapter.preprocess(challenged.detach().clone()))
            candidate_predictions = self.model_runner.predict(candidate_model, candidate_adapter.preprocess(challenged.detach().clone()))
            self._validate_predictions(baseline_predictions, images.shape[0], baseline_adapter.metadata.num_classes)
            self._validate_predictions(candidate_predictions, images.shape[0], candidate_adapter.metadata.num_classes)
            baseline_correct += int((baseline_predictions == labels).sum().item())
            candidate_correct += int((candidate_predictions == labels).sum().item())
            sample_indices.extend(range(total, total + images.shape[0]))
            total += images.shape[0]
        if total == 0:
            raise ExperimentExecutionError("dataset produced no examples for this experiment")
        baseline_score, candidate_score = baseline_correct / total, candidate_correct / total
        delta = candidate_score - baseline_score
        status = "failure" if delta <= self.config.failure_threshold else "pass"
        summary = EvaluationResult(
            evaluation_id=f"{self.config.experiment_id}:{challenge_spec.challenge_id}",
            experiment_id=self.config.experiment_id,
            model=self.config.candidate_model,
            baseline=self.config.baseline_model,
            candidate=self.config.candidate_model,
            challenge=challenge_spec,
            baseline_score=baseline_score,
            candidate_score=candidate_score,
            threshold=self.config.failure_threshold,
            status=status,
            seed=challenge_spec.seed,
            threshold_comparison=self.config.threshold_comparison,
        )
        return ComparisonExperimentResult(summary, total, baseline_correct, candidate_correct, challenge_spec, class_space, tuple(sample_indices))

    def _validate_compatibility(self, baseline: ModelAdapter, candidate: ModelAdapter, dataset: DatasetAdapter) -> None:
        try:
            validate_model_dataset_compatibility(baseline, dataset)
            validate_model_dataset_compatibility(candidate, dataset)
        except Exception as exc:
            raise ExperimentCompatibilityError(str(exc)) from exc
        dataset_space = ClassSpace(dataset.metadata.class_names)
        for name, declared in (("baseline", self.config.baseline_class_space), ("candidate", self.config.candidate_class_space)):
            if declared is not None and declared != dataset_space:
                raise ExperimentCompatibilityError(f"{name} class ordering does not match dataset class ordering")
            if declared is None and not self.config.trust_dataset_class_order:
                raise ExperimentCompatibilityError(f"{name} class ordering is required when trust_dataset_class_order=False")

    def _challenge_for(self, spec: ChallengeSpec):
        if spec.type == "clean":
            return None
        try:
            return self._CHALLENGES[spec.type]()
        except KeyError as exc:
            raise ExperimentExecutionError(f"unsupported challenge type '{spec.type}'") from exc

    @staticmethod
    def _validate_predictions(predictions: Tensor, batch_size: int, num_classes: int) -> None:
        if predictions.ndim != 1 or predictions.shape[0] != batch_size:
            raise ExperimentExecutionError("ModelRunner predictions must align with the batch")
        if torch.any(predictions < 0) or torch.any(predictions >= num_classes):
            raise ExperimentExecutionError("model output class indices are incompatible with declared num_classes")
