import torch
from torch import nn

from core.runner import ModelRunner


class ObservingModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.grad_enabled_during_forward: bool | None = None
        self.training_during_forward: bool | None = None

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.grad_enabled_during_forward = torch.is_grad_enabled()
        self.training_during_forward = self.training
        return inputs


def test_runner_returns_class_predictions_in_eval_without_grad() -> None:
    model = ObservingModel()
    model.train()
    inputs = torch.tensor([[3.0, 1.0], [0.0, 2.0]])

    predictions = ModelRunner().predict(model, inputs)

    assert predictions.tolist() == [0, 1]
    assert predictions.dtype == torch.long
    assert predictions.device.type == "cpu"
    assert model.training is False
    assert model.training_during_forward is False
    assert model.grad_enabled_during_forward is False
