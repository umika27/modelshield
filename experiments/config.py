"""Typed configuration and explicit class-space policy for one comparison."""

from __future__ import annotations

from dataclasses import dataclass

from core.schemas import ModelMetadata


@dataclass(frozen=True)
class ClassSpace:
    """An ordered class identity space; ordering is semantically significant."""

    class_names: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.class_names or len(set(self.class_names)) != len(self.class_names):
            raise ValueError("class_names must be non-empty and unique")


@dataclass(frozen=True)
class ExperimentConfig:
    """Deterministic configuration for one real classification comparison."""

    experiment_id: str
    baseline_model: ModelMetadata
    candidate_model: ModelMetadata
    batch_size: int = 32
    metric: str = "classification_accuracy"
    failure_threshold: float = -0.15
    threshold_comparison: str = "less_than_or_equal"
    seed: int = 42
    max_samples: int | None = None
    baseline_class_space: ClassSpace | None = None
    candidate_class_space: ClassSpace | None = None
    trust_dataset_class_order: bool = True

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise ValueError("experiment_id must not be empty")
        if self.baseline_model.role != "baseline" or self.candidate_model.role != "candidate":
            raise ValueError("baseline_model and candidate_model must use their matching roles")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.metric != "classification_accuracy":
            raise ValueError("only classification_accuracy is supported")
        if self.threshold_comparison != "less_than_or_equal":
            raise ValueError("only less_than_or_equal threshold comparison is supported")
        if not -1.0 <= self.failure_threshold <= 0.0:
            raise ValueError("failure_threshold must be between -1.0 and 0.0")
        if self.max_samples is not None and self.max_samples <= 0:
            raise ValueError("max_samples must be positive when provided")
