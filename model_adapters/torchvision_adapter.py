"""Offline Torchvision image-classification adapter."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import torch
from torch import Tensor, nn
from torch.nn import functional as F
from torchvision import models

from .base import AdapterMetadata, ModelAdapter
from .exceptions import CheckpointLoadError, InvalidCheckpointError, UnsupportedArchitectureError
from .preprocessing import IMAGENET_PREPROCESSING, PreprocessingSpec


class TorchvisionModelAdapter(ModelAdapter):
    """Load supported Torchvision classifiers without downloading weights."""

    _BUILDERS = {
        "resnet18": models.resnet18,
        "resnet50": models.resnet50,
        "mobilenet_v3_small": models.mobilenet_v3_small,
        "efficientnet_b0": models.efficientnet_b0,
    }

    def __init__(
        self,
        *,
        architecture: str,
        num_classes: int,
        checkpoint_path: str | Path | None = None,
        device: str | torch.device = "cpu",
        strict: bool = True,
    ) -> None:
        if architecture not in self._BUILDERS:
            supported = ", ".join(self.supported_architectures())
            raise UnsupportedArchitectureError(f"unsupported Torchvision architecture '{architecture}'; supported: {supported}")
        if isinstance(num_classes, bool) or not isinstance(num_classes, int) or num_classes <= 0:
            raise ValueError("num_classes must be a positive integer")
        self.architecture = architecture
        self.num_classes = num_classes
        self.checkpoint_path = self.normalize_path(checkpoint_path)
        self.device = torch.device(device)
        self.strict = strict
        self._class_names: tuple[str, ...] | None = None

    @property
    def class_names(self) -> tuple[str, ...] | None:
        """Ordered class semantics read from a new-format checkpoint, if present."""
        return self._class_names

    @classmethod
    def supported_architectures(cls) -> tuple[str, ...]:
        """Return supported architecture names in deterministic order."""
        return tuple(sorted(cls._BUILDERS))

    @property
    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            framework="pytorch",
            backend="torchvision",
            architecture=self.architecture,
            num_classes=self.num_classes,
            checkpoint_path=str(self.checkpoint_path) if self.checkpoint_path is not None else None,
        )

    @property
    def preprocessing(self) -> PreprocessingSpec:
        """Explicit offline ImageNet preprocessing for all supported classifiers."""
        return IMAGENET_PREPROCESSING

    def preprocess(self, images: Tensor) -> Tensor:
        """Resize and normalize canonical NCHW RGB float32 images without mutation."""
        self._validate_canonical_batch(images)
        resized = F.interpolate(images.detach().clone(), size=self.preprocessing.input_size, mode="bilinear", align_corners=False)
        mean = resized.new_tensor(self.preprocessing.mean).view(1, 3, 1, 1)
        std = resized.new_tensor(self.preprocessing.std).view(1, 3, 1, 1)
        return (resized - mean) / std

    def load(self) -> nn.Module:
        """Build the requested classifier and strictly load an optional checkpoint."""
        model = self._build_model()
        if self.checkpoint_path is not None:
            self._load_checkpoint(model, self.checkpoint_path)
        return model.to(self.device).eval()

    def _build_model(self) -> nn.Module:
        builder = self._BUILDERS[self.architecture]
        # Explicit None guarantees fully offline construction with random weights.
        model = builder(weights=None)
        if self.architecture.startswith("resnet"):
            model.fc = nn.Linear(model.fc.in_features, self.num_classes)
        elif self.architecture in {"mobilenet_v3_small", "efficientnet_b0"}:
            final_layer = model.classifier[-1]
            if not isinstance(final_layer, nn.Linear):
                raise RuntimeError(f"unexpected {self.architecture} classifier layout")
            model.classifier[-1] = nn.Linear(final_layer.in_features, self.num_classes)
        else:  # Defensive guard for future registry additions.
            raise UnsupportedArchitectureError(f"no classifier replacement configured for '{self.architecture}'")
        return model

    @staticmethod
    def _validate_canonical_batch(images: Tensor) -> None:
        if not isinstance(images, Tensor):
            raise TypeError("images must be a torch.Tensor")
        if images.dtype != torch.float32:
            raise ValueError("images dtype must be torch.float32")
        if images.ndim != 4 or images.shape[1] != 3:
            raise ValueError("images must have shape (N, 3, H, W)")
        if images.shape[0] == 0 or images.shape[2] == 0 or images.shape[3] == 0:
            raise ValueError("images must have non-empty batch and spatial dimensions")
        if not torch.isfinite(images).all() or torch.any(images < 0) or torch.any(images > 1):
            raise ValueError("images must contain finite values in [0, 1]")

    def _load_checkpoint(self, model: nn.Module, path: Path) -> None:
        if not path.is_file():
            raise CheckpointLoadError(f"checkpoint file does not exist: {path}")
        try:
            checkpoint = torch.load(path, map_location="cpu", weights_only=True)
        except Exception as exc:
            raise CheckpointLoadError(f"unable to read checkpoint '{path}': {exc}") from exc
        state_dict = self._normalize_checkpoint(checkpoint)
        metadata = checkpoint.get("metadata") if isinstance(checkpoint, Mapping) else None
        if isinstance(metadata, Mapping) and isinstance(metadata.get("class_names"), list) and all(isinstance(name, str) for name in metadata["class_names"]):
            self._class_names = tuple(metadata["class_names"])
        try:
            model.load_state_dict(state_dict, strict=self.strict)
        except RuntimeError as exc:
            mode = "strict" if self.strict else "non-strict"
            raise CheckpointLoadError(f"{mode} checkpoint load failed for '{path}': {exc}") from exc

    @staticmethod
    def _normalize_checkpoint(checkpoint: Any) -> dict[str, Tensor]:
        if not isinstance(checkpoint, Mapping):
            raise InvalidCheckpointError("checkpoint must be a state_dict mapping or a supported wrapper mapping")
        if "state_dict" in checkpoint or "model_state_dict" in checkpoint:
            selected_key = "state_dict" if "state_dict" in checkpoint else "model_state_dict"
            state_dict = checkpoint[selected_key]
            if not isinstance(state_dict, Mapping):
                raise InvalidCheckpointError(f"checkpoint field '{selected_key}' must be a mapping")
        else:
            state_dict = checkpoint

        normalized: dict[str, Tensor] = {}
        for key, value in state_dict.items():
            if not isinstance(key, str) or not isinstance(value, Tensor):
                raise InvalidCheckpointError("state_dict keys must be strings and values must be tensors")
            normalized_key = key.removeprefix("module.")
            if normalized_key in normalized:
                raise InvalidCheckpointError(f"duplicate state_dict key after DataParallel prefix removal: {normalized_key}")
            normalized[normalized_key] = value
        if not normalized:
            raise InvalidCheckpointError("state_dict must not be empty")
        return normalized
