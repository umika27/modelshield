"""Additional real-experiment evidence around the shared EvaluationResult."""

from __future__ import annotations

from dataclasses import dataclass

from core.schemas import ChallengeSpec, EvaluationResult

from .config import ClassSpace


@dataclass(frozen=True)
class ComparisonExperimentResult:
    """Dataset-level comparison evidence; EvaluationResult remains canonical summary."""

    evaluation_result: EvaluationResult
    num_samples: int
    baseline_correct: int
    candidate_correct: int
    challenge: ChallengeSpec
    class_space: ClassSpace
    sample_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.num_samples <= 0 or len(self.sample_indices) != self.num_samples:
            raise ValueError("num_samples and sample_indices must describe evaluated examples")
        if not 0 <= self.baseline_correct <= self.num_samples or not 0 <= self.candidate_correct <= self.num_samples:
            raise ValueError("correct counts must be within evaluated sample range")
