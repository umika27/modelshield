"""Local ImageFolder adapter emitting canonical RGB ModelShield tensors."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import datasets, transforms

from .base import DatasetAdapter, ValidatedClassificationDataset
from .exceptions import DatasetLoadError
from .metadata import DatasetMetadata


class ImageFolderAdapter(DatasetAdapter):
    """Load local class folders without label remapping or normalization.

    ImageFolder batches require equal image dimensions. Provide ``image_size``
    for mixed-size source images so they can be deterministically stacked.
    """

    def __init__(self, *, root: str | Path, split: str = "unspecified", image_size: tuple[int, int] | None = None) -> None:
        self.root, self.split, self.image_size = Path(root), split, image_size

    def load(self) -> Dataset:
        if not self.root.is_dir():
            raise DatasetLoadError(f"ImageFolder root does not exist or is not a directory: {self.root}")
        if not any(path.is_dir() for path in self.root.iterdir()):
            raise DatasetLoadError(f"ImageFolder root has no class folders: {self.root}")
        steps = [transforms.Resize(self.image_size)] if self.image_size is not None else []
        steps.append(transforms.ToTensor())
        try:
            source = datasets.ImageFolder(str(self.root), loader=self._rgb_loader, transform=transforms.Compose(steps))
        except Exception as exc:
            raise DatasetLoadError(f"unable to load ImageFolder dataset from '{self.root}': {exc}") from exc
        if not source.classes or not source.samples:
            raise DatasetLoadError(f"ImageFolder dataset is empty: {self.root}")
        self._dataset = ValidatedClassificationDataset(source, len(source.classes))
        self._metadata = DatasetMetadata(
            dataset_name="imagefolder", task_type="image_classification", split=self.split,
            num_classes=len(source.classes), class_names=tuple(source.classes),
            class_to_idx=dict(source.class_to_idx), num_samples=len(self._dataset),
        )
        return self._dataset

    @staticmethod
    def _rgb_loader(path: str) -> Image.Image:
        with Image.open(path) as image:
            return image.convert("RGB")
