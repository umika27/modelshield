import pytest
import torch

from core.metrics import classification_accuracy


def test_classification_accuracy_returns_fraction() -> None:
    assert classification_accuracy([0, 1, 1, 0], [0, 0, 1, 0]) == 0.75
    assert classification_accuracy(torch.tensor([0, 1]), torch.tensor([0, 1])) == 1.0


@pytest.mark.parametrize(
    ("predictions", "labels", "error"),
    [
        ([], [], "must not be empty"),
        ([0, 1], [0], "compatible lengths"),
        ([[0, 1]], [0], "one-dimensional"),
        ("01", [0, 1], "one-dimensional sequence"),
    ],
)
def test_classification_accuracy_rejects_invalid_inputs(predictions, labels, error: str) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        classification_accuracy(predictions, labels)
