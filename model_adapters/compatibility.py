"""Obvious model/dataset compatibility checks before real experiments run."""

from __future__ import annotations

from dataset_adapters.base import DatasetAdapter

from .base import ModelAdapter
from .exceptions import ModelDatasetCompatibilityError


def validate_model_dataset_compatibility(model_adapter: ModelAdapter, dataset_adapter: DatasetAdapter) -> None:
    """Require matching class counts; class-semantic matching remains future work."""
    if model_adapter.metadata.num_classes != dataset_adapter.metadata.num_classes:
        raise ModelDatasetCompatibilityError(
            f"model expects {model_adapter.metadata.num_classes} classes but dataset provides {dataset_adapter.metadata.num_classes} classes"
        )
