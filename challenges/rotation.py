"""Deterministic image rotation challenge."""

from __future__ import annotations

import math
from typing import Any, Mapping

import torch
from torch import Tensor
from torch.nn import functional as F

from .base import ImageChallenge


class RotationChallenge(ImageChallenge):
    """Rotate images by ``degrees`` in the inclusive range [-180, 180]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        del seed
        images = self.validate_images(inputs)
        degrees = self.numeric_parameter(parameters, "degrees", minimum=-180.0, maximum=180.0)
        if degrees == 0:
            return images
        radians = math.radians(degrees)
        cosine, sine = math.cos(radians), math.sin(radians)
        theta = images.new_tensor([[cosine, -sine, 0.0], [sine, cosine, 0.0]])
        theta = theta.unsqueeze(0).expand(images.shape[0], -1, -1)
        grid = F.affine_grid(theta, images.shape, align_corners=False)
        return F.grid_sample(images, grid, mode="bilinear", padding_mode="border", align_corners=False).clamp(0, 1)
