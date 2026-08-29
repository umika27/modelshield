"""Small explicit factory for supported model adapter backends."""

from __future__ import annotations

from pathlib import Path

import torch

from .base import ModelAdapter
from .exceptions import UnsupportedBackendError
from .torchvision_adapter import TorchvisionModelAdapter


def create_model_adapter(
    *,
    backend: str,
    architecture: str,
    num_classes: int,
    checkpoint_path: str | Path | None = None,
    device: str | torch.device = "cpu",
    strict: bool = True,
) -> ModelAdapter:
    """Create an adapter from an explicit backend registry, never dynamic imports."""
    if backend != "torchvision":
        raise UnsupportedBackendError("unsupported backend '{}'; supported: torchvision".format(backend))
    return TorchvisionModelAdapter(
        architecture=architecture,
        num_classes=num_classes,
        checkpoint_path=checkpoint_path,
        device=device,
        strict=strict,
    )


def supported_architectures(backend: str = "torchvision") -> tuple[str, ...]:
    """Return the architectures supported by one registered backend."""
    if backend != "torchvision":
        raise UnsupportedBackendError("unsupported backend '{}'; supported: torchvision".format(backend))
    return TorchvisionModelAdapter.supported_architectures()
