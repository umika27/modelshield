"""Serializable metadata for a loaded image-classification dataset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class DatasetMetadata:
    """Stable dataset identity and class-order information."""

    dataset_name: str
    task_type: str
    split: str
    num_classes: int
    class_names: tuple[str, ...]
    class_to_idx: Mapping[str, int]
    num_samples: int

    def __post_init__(self) -> None:
        if self.task_type != "image_classification":
            raise ValueError("task_type must be 'image_classification'")
        if self.num_classes <= 0 or self.num_samples <= 0:
            raise ValueError("num_classes and num_samples must be positive")
        if self.num_classes != len(self.class_names):
            raise ValueError("num_classes must equal the number of class_names")
        if set(self.class_to_idx) != set(self.class_names):
            raise ValueError("class_to_idx keys must match class_names")
        if tuple(self.class_to_idx[name] for name in self.class_names) != tuple(range(self.num_classes)):
            raise ValueError("class_to_idx must preserve class_names ordering")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name, "task_type": self.task_type, "split": self.split,
            "num_classes": self.num_classes, "class_names": list(self.class_names),
            "class_to_idx": dict(self.class_to_idx), "num_samples": self.num_samples,
        }
