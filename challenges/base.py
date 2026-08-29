"""Shared validation and interface for tensor image challenges."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from numbers import Real
from typing import Any, Mapping

import torch
from torch import Tensor


class ImageChallenge(ABC):
    """A controlled transform of a batch of ``(N, C, H, W)`` images in [0, 1]."""

    @abstractmethod
    def apply(
        self,
        inputs: Tensor,
        parameters: Mapping[str, Any],
        seed: int | None = None,
    ) -> Tensor:
        """Return a transformed copy of ``inputs`` without mutating it."""

    @staticmethod
    def validate_images(inputs: Tensor) -> Tensor:
        if not isinstance(inputs, Tensor):
            raise TypeError("inputs must be a torch.Tensor")
        if inputs.ndim != 4:
            raise ValueError("inputs must have image-batch shape (N, C, H, W)")
        if not inputs.is_floating_point():
            raise TypeError("inputs must use a floating-point dtype")
        if inputs.shape[0] == 0 or inputs.shape[1] == 0 or inputs.shape[2] == 0 or inputs.shape[3] == 0:
            raise ValueError("inputs must have non-empty batch, channel, height, and width dimensions")
        if not torch.isfinite(inputs).all():
            raise ValueError("inputs must contain only finite values")
        if torch.any(inputs < 0) or torch.any(inputs > 1):
            raise ValueError("inputs must contain image values in the range [0, 1]")
        return inputs.detach().clone()

    @staticmethod
    def numeric_parameter(
        parameters: Mapping[str, Any],
        name: str,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        if not isinstance(parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        if name not in parameters:
            raise ValueError(f"missing required parameter: {name}")
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"parameter '{name}' must be numeric")
        value = float(value)
        if not math.isfinite(value) or not minimum <= value <= maximum:
            raise ValueError(f"parameter '{name}' must be between {minimum} and {maximum}")
        return value
