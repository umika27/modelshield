"""Explicit registry for supported local image-classification datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import DatasetAdapter
from .cifar10 import CIFAR10Adapter
from .exceptions import UnsupportedDatasetTypeError
from .imagefolder import ImageFolderAdapter


def supported_dataset_types() -> tuple[str, ...]:
    """Return supported dataset type names in deterministic order."""
    return "cifar10", "imagefolder"


def create_dataset_adapter(*, dataset_type: str, root: str | Path, **kwargs: Any) -> DatasetAdapter:
    """Create a dataset adapter through an explicit, offline-safe registry."""
    if dataset_type == "cifar10":
        return CIFAR10Adapter(root=root, **kwargs)
    if dataset_type == "imagefolder":
        return ImageFolderAdapter(root=root, **kwargs)
    raise UnsupportedDatasetTypeError(f"unsupported dataset type '{dataset_type}'; supported: {', '.join(supported_dataset_types())}")
