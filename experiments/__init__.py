"""Real baseline-versus-candidate experiment orchestration."""

from .config import ClassSpace, ExperimentConfig
from .exceptions import ExperimentCompatibilityError, ExperimentExecutionError
from .result import ComparisonExperimentResult
from .runner import ComparisonExperimentRunner

__all__ = [
    "ClassSpace", "ComparisonExperimentResult", "ComparisonExperimentRunner",
    "ExperimentCompatibilityError", "ExperimentConfig", "ExperimentExecutionError",
]
