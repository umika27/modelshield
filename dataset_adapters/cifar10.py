"""Offline-first CIFAR-10 adapter emitting canonical ModelShield tensors."""

from __future__ import annotations

from pathlib import Path

from torch.utils.data import Dataset
from torchvision import datasets, transforms

from .base import DatasetAdapter, ValidatedClassificationDataset
from .exceptions import DatasetLoadError
from .metadata import DatasetMetadata


class CIFAR10Adapter(DatasetAdapter):
    """Load local CIFAR-10 data; downloads occur only with explicit opt-in."""

    CLASS_NAMES = ("airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck")

    def __init__(self, *, root: str | Path, split: str = "test", download: bool = False, image_size: tuple[int, int] | None = None) -> None:
        if split not in {"train", "test"}:
            raise ValueError("CIFAR-10 split must be 'train' or 'test'")
        self.root, self.split, self.download, self.image_size = Path(root), split, download, image_size

    def load(self) -> Dataset:
        steps = [transforms.Resize(self.image_size)] if self.image_size is not None else []
        steps.append(transforms.ToTensor())
        try:
            source = datasets.CIFAR10(str(self.root), train=self.split == "train", download=self.download, transform=transforms.Compose(steps))
        except Exception as exc:
            note = " Set download=True to explicitly permit a Torchvision download." if not self.download else ""
            raise DatasetLoadError(f"unable to load CIFAR-10 from '{self.root}'.{note}") from exc
        self._dataset = ValidatedClassificationDataset(source, len(self.CLASS_NAMES))
        self._metadata = DatasetMetadata(
            dataset_name="cifar10", task_type="image_classification", split=self.split,
            num_classes=len(self.CLASS_NAMES), class_names=self.CLASS_NAMES,
            class_to_idx={name: index for index, name in enumerate(self.CLASS_NAMES)}, num_samples=len(self._dataset),
        )
        return self._dataset
