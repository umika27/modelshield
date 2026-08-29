"""Seedable additive Gaussian noise challenge."""

from __future__ import annotations

from typing import Any, Mapping

import torch
from torch import Tensor

from .base import ImageChallenge


class NoiseChallenge(ImageChallenge):
    """Add Gaussian noise with standard-deviation ``level`` in [0, 1]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        images = self.validate_images(inputs)
        level = self.numeric_parameter(parameters, "level", minimum=0.0, maximum=1.0)
        if level == 0:
            return images
        if seed is None:
            noise = torch.randn_like(images)
        else:
            generator = torch.Generator(device=images.device)
            generator.manual_seed(seed)
            noise = torch.randn(images.shape, dtype=images.dtype, device=images.device, generator=generator)
        return (images + (noise * level)).clamp(0, 1)
