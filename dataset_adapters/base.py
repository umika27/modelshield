"""Common canonical image validation and deterministic loader behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch
from torch import Tensor
from torch.utils.data import DataLoader, Dataset

from .exceptions import DatasetValidationError
from .metadata import DatasetMetadata


def validate_canonical_image(image: Tensor) -> Tensor:
    """Validate one RGB image in the canonical CHW float32 [0, 1] contract."""
    if not isinstance(image, Tensor):
        raise DatasetValidationError("image must be a torch.Tensor")
    if image.dtype != torch.float32:
        raise DatasetValidationError("image dtype must be torch.float32")
    if image.ndim != 3 or image.shape[0] != 3:
        raise DatasetValidationError("image must have shape (3, H, W)")
    if image.shape[1] == 0 or image.shape[2] == 0:
        raise DatasetValidationError("image height and width must be positive")
    if not torch.isfinite(image).all() or torch.any(image < 0) or torch.any(image > 1):
        raise DatasetValidationError("image values must be finite and in [0, 1]")
    return image


def validate_canonical_batch(images: Tensor) -> Tensor:
    """Validate an RGB batch in the canonical NCHW float32 [0, 1] contract."""
    if not isinstance(images, Tensor):
        raise DatasetValidationError("images must be a torch.Tensor")
    if images.dtype != torch.float32:
        raise DatasetValidationError("images dtype must be torch.float32")
    if images.ndim != 4 or images.shape[1] != 3:
        raise DatasetValidationError("images must have shape (N, 3, H, W)")
    if images.shape[0] == 0 or images.shape[2] == 0 or images.shape[3] == 0:
        raise DatasetValidationError("batch, height, and width dimensions must be positive")
    if not torch.isfinite(images).all() or torch.any(images < 0) or torch.any(images > 1):
        raise DatasetValidationError("image values must be finite and in [0, 1]")
    return images


class ValidatedClassificationDataset(Dataset):
    """Validate samples emitted by a Torchvision dataset without changing values."""

    def __init__(self, source: Dataset, num_classes: int) -> None:
        self.source, self.num_classes = source, num_classes

    def __len__(self) -> int:
        return len(self.source)

    def __getitem__(self, index: int) -> tuple[Tensor, int]:
        image, label = self.source[index]
        validate_canonical_image(image)
        if isinstance(label, bool) or not isinstance(label, int) or not 0 <= label < self.num_classes:
            raise DatasetValidationError(f"label must be an integer in [0, {self.num_classes - 1}]")
        return image, label


class DatasetAdapter(ABC):
    """Load a classification dataset and build deterministic PyTorch loaders."""

    _dataset: Dataset | None = None
    _metadata: DatasetMetadata | None = None

    @property
    def dataset(self) -> Dataset:
        if self._dataset is None:
            raise DatasetValidationError("dataset is not loaded; call load() first")
        return self._dataset

    @property
    def metadata(self) -> DatasetMetadata:
        if self._metadata is None:
            raise DatasetValidationError("dataset metadata is unavailable; call load() first")
        return self._metadata

    @abstractmethod
    def load(self) -> Dataset:
        """Load the underlying local dataset into the canonical contract."""

    def create_dataloader(self, *, batch_size: int, shuffle: bool = False, num_workers: int = 0, seed: int | None = None) -> DataLoader:
        """Create a DataLoader with optional local-generator shuffle determinism."""
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
        if num_workers < 0:
            raise ValueError("num_workers must not be negative")
        generator = None
        if shuffle and seed is not None:
            generator = torch.Generator().manual_seed(seed)
        return DataLoader(self.dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, generator=generator)
