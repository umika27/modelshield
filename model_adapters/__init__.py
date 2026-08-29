"""Offline model-loading adapters for ModelShield evaluation."""

from .base import AdapterMetadata, ModelAdapter
from .exceptions import CheckpointLoadError, InvalidCheckpointError, UnsupportedArchitectureError, UnsupportedBackendError
from .registry import create_model_adapter, supported_architectures
from .torchvision_adapter import TorchvisionModelAdapter

__all__ = [
    "AdapterMetadata",
    "CheckpointLoadError",
    "InvalidCheckpointError",
    "ModelAdapter",
    "TorchvisionModelAdapter",
    "UnsupportedArchitectureError",
    "UnsupportedBackendError",
    "create_model_adapter",
    "supported_architectures",
]
