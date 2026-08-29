"""Gaussian blur challenge."""

from __future__ import annotations

import math
from typing import Any, Mapping

import torch
from torch import Tensor
from torch.nn import functional as F

from .base import ImageChallenge


def gaussian_blur(inputs: Tensor, severity: float) -> Tensor:
    """Apply channel-wise Gaussian blur; severity zero is an identity copy."""
    if severity == 0:
        return inputs.clone()
    sigma = 0.5 + (2.0 * severity)
    radius = max(1, math.ceil(3 * sigma))
    coordinates = torch.arange(-radius, radius + 1, device=inputs.device, dtype=inputs.dtype)
    kernel_1d = torch.exp(-(coordinates.square()) / (2 * sigma * sigma))
    kernel_1d = kernel_1d / kernel_1d.sum()
    kernel_2d = torch.outer(kernel_1d, kernel_1d)
    channels = inputs.shape[1]
    kernel = kernel_2d.expand(channels, 1, -1, -1)
    padded = F.pad(inputs, (radius, radius, radius, radius), mode="replicate")
    return F.conv2d(padded, kernel, groups=channels)


class BlurChallenge(ImageChallenge):
    """Blur images with ``severity`` in the inclusive range [0, 1]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        del seed
        images = self.validate_images(inputs)
        severity = self.numeric_parameter(parameters, "severity", minimum=0.0, maximum=1.0)
        return gaussian_blur(images, severity).clamp(0, 1)
