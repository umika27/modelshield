from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from core.schemas.failure import FailureRecord, ModelRef
from core.schemas.regression import RegressionRecord


@runtime_checkable
class FailureStoreInterface(Protocol):
    """Interface for failure storage / memory layer.
    Allows database, in-memory, or file-based memory layers to be seamlessly connected.
    """

    def get_failure(self, failure_id: str) -> Optional[FailureRecord]:
        """Retrieve a failure record by its unique ID."""
        ...

    def list_failures(self, verified_only: bool = True) -> List[FailureRecord]:
        """List all stored failure records, optionally filtering by verified status."""
        ...

    def save_failure(self, failure: FailureRecord) -> None:
        """Persist a failure record."""
        ...


@runtime_checkable
class RegressionStoreInterface(Protocol):
    """Interface for regression suite persistence.
    Allows team members to plug in different database or registry backends.
    """

    def get_regression(self, regression_id: str) -> Optional[RegressionRecord]:
        """Retrieve a regression record by ID."""
        ...

    def list_regressions(self, enabled_only: bool = True) -> List[RegressionRecord]:
        """List regression records, optionally filtering to enabled tests only."""
        ...

    def save_regression(self, regression: RegressionRecord) -> None:
        """Persist a regression record."""
        ...

    def set_enabled(self, regression_id: str, enabled: bool) -> bool:
        """Enable or disable a specific regression test."""
        ...


@runtime_checkable
class EvaluatorInterface(Protocol):
    """Interface for evaluating a model under a regression test condition.
    Decoupled from ML framework specifics (PyTorch, ONNX, API endpoints, etc.).
    """

    def evaluate_condition(
        self,
        candidate_model: ModelRef,
        condition_type: str,
        parameters: Dict[str, Any],
        metric_name: str,
    ) -> float:
        """Evaluate candidate model under the given challenge condition and return the metric score."""
        ...
