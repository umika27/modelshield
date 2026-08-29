"""Core evaluation primitives for ModelShield."""

from .evaluator import EvaluationEngine
from .metrics import classification_accuracy
from .runner import ModelRunner
from .schemas import ChallengeSpec, EvaluationResult, ExperimentMetadata, ModelMetadata

__all__ = [
    "ChallengeSpec",
    "EvaluationEngine",
    "EvaluationResult",
    "ExperimentMetadata",
    "ModelMetadata",
    "ModelRunner",
    "classification_accuracy",
]
