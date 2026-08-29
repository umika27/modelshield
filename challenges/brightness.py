"""Brightness challenge."""

from __future__ import annotations

from typing import Any, Mapping

from torch import Tensor

from .base import ImageChallenge


class BrightnessChallenge(ImageChallenge):
    """Scale brightness by ``factor`` in the inclusive range [0, 2]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        del seed
        images = self.validate_images(inputs)
        factor = self.numeric_parameter(parameters, "factor", minimum=0.0, maximum=2.0)
        return (images * factor).clamp(0, 1)
