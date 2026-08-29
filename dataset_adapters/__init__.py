"""Dataset adapters that emit validated canonical ModelShield image tensors."""

from .base import DatasetAdapter, validate_canonical_batch, validate_canonical_image
from .cifar10 import CIFAR10Adapter
from .exceptions import DatasetLoadError, DatasetValidationError, UnsupportedDatasetTypeError
from .imagefolder import ImageFolderAdapter
from .metadata import DatasetMetadata
from .registry import create_dataset_adapter, supported_dataset_types

__all__ = [
    "CIFAR10Adapter", "DatasetAdapter", "DatasetLoadError", "DatasetMetadata",
    "DatasetValidationError", "ImageFolderAdapter", "UnsupportedDatasetTypeError",
    "create_dataset_adapter", "supported_dataset_types", "validate_canonical_batch", "validate_canonical_image",
]
