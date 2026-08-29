"""Offline model-loading adapters for ModelShield evaluation."""

from .base import AdapterMetadata, ModelAdapter
from .compatibility import validate_model_dataset_compatibility
from .exceptions import (
    CheckpointLoadError,
    InvalidCheckpointError,
    ModelDatasetCompatibilityError,
    UnsupportedArchitectureError,
    UnsupportedBackendError,
)
from .preprocessing import PreprocessingSpec
from .registry import create_model_adapter, supported_architectures
from .torchvision_adapter import TorchvisionModelAdapter

__all__ = [
    "AdapterMetadata",
    "CheckpointLoadError",
    "InvalidCheckpointError",
    "ModelAdapter",
    "ModelDatasetCompatibilityError",
    "PreprocessingSpec",
    "TorchvisionModelAdapter",
    "UnsupportedArchitectureError",
    "UnsupportedBackendError",
    "create_model_adapter",
    "supported_architectures",
    "validate_model_dataset_compatibility",
]
