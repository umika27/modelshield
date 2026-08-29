"""Common types for model-loading adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from torch import nn


@dataclass(frozen=True)
class AdapterMetadata:
    """Adapter-specific metadata kept separate from shared ModelMetadata."""

    framework: str
    backend: str
    architecture: str
    num_classes: int
    checkpoint_path: str | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable metadata record."""
        return {
            "framework": self.framework,
            "backend": self.backend,
            "architecture": self.architecture,
            "num_classes": self.num_classes,
            "checkpoint_path": self.checkpoint_path,
        }


class ModelAdapter(ABC):
    """Construct a model for the existing ModelRunner to execute."""

    @property
    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Return stable adapter configuration metadata."""

    @abstractmethod
    def load(self) -> nn.Module:
        """Instantiate, optionally checkpoint-load, and return a module."""

    @staticmethod
    def normalize_path(path: str | Path | None) -> Path | None:
        """Normalize an optional checkpoint path without accessing it."""
        return Path(path) if path is not None else None
