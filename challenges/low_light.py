"""Low-light challenge."""

from __future__ import annotations

from typing import Any, Mapping

from torch import Tensor

from .base import ImageChallenge


class LowLightChallenge(ImageChallenge):
    """Darken images by a ``brightness`` multiplier in the range [0, 1]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        del seed
        images = self.validate_images(inputs)
        brightness = self.numeric_parameter(parameters, "brightness", minimum=0.0, maximum=1.0)
        return (images * brightness).clamp(0, 1)
