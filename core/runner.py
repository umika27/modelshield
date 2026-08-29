"""Small, CPU-safe PyTorch inference abstraction."""

from __future__ import annotations

import torch
from torch import Tensor, nn


class ModelRunner:
    """Run an injected classification model without coupling to an architecture."""

    def __init__(self, device: str | torch.device = "cpu") -> None:
        self.device = torch.device(device)
        if self.device.type != "cpu" and not torch.cuda.is_available():
            raise ValueError(f"requested device is unavailable: {self.device}")

    def predict(self, model: nn.Module, inputs: Tensor) -> Tensor:
        """Return CPU class-index predictions with shape ``(batch_size,)``.

        Models may return multiclass logits of shape ``(N, C)`` or binary logits
        of shape ``(N,)``. The caller owns model construction and data loading.
        """
        if not isinstance(model, nn.Module):
            raise TypeError("model must be a torch.nn.Module")
        if not isinstance(inputs, Tensor):
            raise TypeError("inputs must be a torch.Tensor")
        if inputs.ndim == 0:
            raise ValueError("inputs must include a batch dimension")

        model = model.to(self.device)
        model.eval()
        with torch.no_grad():
            outputs = model(inputs.to(self.device))

        if not isinstance(outputs, Tensor):
            raise TypeError("model output must be a torch.Tensor")
        if outputs.ndim == 1:
            predictions = (outputs >= 0).to(torch.long)
        elif outputs.ndim == 2:
            if outputs.shape[0] != inputs.shape[0] or outputs.shape[1] == 0:
                raise ValueError("model output must have shape (batch_size, classes)")
            predictions = outputs.argmax(dim=1)
        else:
            raise ValueError("model output must have shape (N,) or (N, C)")
        return predictions.detach().to("cpu", dtype=torch.long)
