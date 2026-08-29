"""Model-specific preprocessing applied only after image-space challenges."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math


@dataclass(frozen=True)
class PreprocessingSpec:
    """Immutable inference preprocessing for canonical RGB image batches."""

    input_size: tuple[int, int]
    mean: tuple[float, float, float]
    std: tuple[float, float, float]

    def __post_init__(self) -> None:
        if len(self.input_size) != 2 or any(not isinstance(value, int) or value <= 0 for value in self.input_size):
            raise ValueError("input_size must contain two positive integers")
        if len(self.mean) != 3 or len(self.std) != 3:
            raise ValueError("mean and std must contain exactly three RGB values")
        if any(not math.isfinite(value) for value in (*self.mean, *self.std)):
            raise ValueError("mean and std values must be finite")
        if any(value <= 0 for value in self.std):
            raise ValueError("std values must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {"input_size": list(self.input_size), "mean": list(self.mean), "std": list(self.std)}


IMAGENET_PREPROCESSING = PreprocessingSpec(
    input_size=(224, 224), mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)
)
