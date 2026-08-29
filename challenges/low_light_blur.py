"""Combined low-light and blur challenge used by the core demonstration."""

from __future__ import annotations

from typing import Any, Mapping

from torch import Tensor

from .base import ImageChallenge
from .blur import gaussian_blur


class LowLightBlurChallenge(ImageChallenge):
    """Darken by ``brightness`` [0, 1] then blur at ``blur`` severity [0, 1]."""

    def apply(self, inputs: Tensor, parameters: Mapping[str, Any], seed: int | None = None) -> Tensor:
        del seed
        images = self.validate_images(inputs)
        brightness = self.numeric_parameter(parameters, "brightness", minimum=0.0, maximum=1.0)
        blur = self.numeric_parameter(parameters, "blur", minimum=0.0, maximum=1.0)
        return gaussian_blur((images * brightness).clamp(0, 1), blur).clamp(0, 1)
