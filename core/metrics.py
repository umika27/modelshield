"""Metrics independent from model execution."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch
from torch import Tensor


def _as_flat_values(values: Sequence[Any] | Tensor, name: str) -> list[Any]:
    if isinstance(values, Tensor):
        if values.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")
        return values.detach().cpu().tolist()
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{name} must be a one-dimensional sequence or torch.Tensor")
    if any(isinstance(value, (list, tuple, Tensor)) for value in values):
        raise ValueError(f"{name} must be one-dimensional")
    return list(values)


def classification_accuracy(predictions: Sequence[Any] | Tensor, labels: Sequence[Any] | Tensor) -> float:
    """Return classification accuracy in ``[0.0, 1.0]`` for matching labels."""
    prediction_values = _as_flat_values(predictions, "predictions")
    label_values = _as_flat_values(labels, "labels")
    if not prediction_values:
        raise ValueError("predictions and labels must not be empty")
    if len(prediction_values) != len(label_values):
        raise ValueError("predictions and labels must have compatible lengths")
    correct = sum(prediction == label for prediction, label in zip(prediction_values, label_values, strict=True))
    return float(correct / len(label_values))
