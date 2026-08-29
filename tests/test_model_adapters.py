from pathlib import Path

import pytest
import torch
from torch import nn

from core.runner import ModelRunner
from model_adapters import (
    CheckpointLoadError,
    TorchvisionModelAdapter,
    UnsupportedArchitectureError,
    create_model_adapter,
    supported_architectures,
)


def make_adapter(architecture: str = "resnet18", **kwargs) -> TorchvisionModelAdapter:
    return TorchvisionModelAdapter(architecture=architecture, num_classes=3, **kwargs)


def test_supported_architecture_list_is_stable() -> None:
    assert supported_architectures() == ("efficientnet_b0", "mobilenet_v3_small", "resnet18", "resnet50")


def test_unsupported_architecture_raises_clear_error() -> None:
    with pytest.raises(UnsupportedArchitectureError, match="unsupported Torchvision architecture"):
        make_adapter("not-a-model")


@pytest.mark.parametrize("architecture", ["resnet18", "resnet50", "mobilenet_v3_small", "efficientnet_b0"])
def test_supported_models_return_modules_with_custom_output_shape(architecture: str) -> None:
    model = make_adapter(architecture).load()

    assert isinstance(model, nn.Module)
    with torch.no_grad():
        output = model(torch.zeros((1, 3, 32, 32)))
    assert output.shape == (1, 3)


def test_resnet_classifier_is_replaced() -> None:
    model = make_adapter("resnet18").load()
    assert model.fc.out_features == 3


@pytest.mark.parametrize("architecture", ["mobilenet_v3_small", "efficientnet_b0"])
def test_non_resnet_classifier_is_replaced(architecture: str) -> None:
    model = make_adapter(architecture).load()
    assert model.classifier[-1].out_features == 3


@pytest.mark.parametrize("wrapper_key", [None, "state_dict", "model_state_dict"])
def test_common_checkpoint_formats_load(tmp_path: Path, wrapper_key: str | None) -> None:
    source = make_adapter().load()
    state_dict = source.state_dict()
    checkpoint = state_dict if wrapper_key is None else {wrapper_key: state_dict}
    path = tmp_path / f"{wrapper_key or 'raw'}.pth"
    torch.save(checkpoint, path)

    loaded = make_adapter(checkpoint_path=path).load()
    assert torch.equal(loaded.state_dict()["fc.weight"], state_dict["fc.weight"])


def test_dataparallel_prefix_is_removed(tmp_path: Path) -> None:
    source = make_adapter().load()
    prefixed = {f"module.{key}": value for key, value in source.state_dict().items()}
    path = tmp_path / "parallel.pth"
    torch.save({"state_dict": prefixed}, path)

    loaded = make_adapter(checkpoint_path=path).load()
    assert torch.equal(loaded.state_dict()["fc.bias"], source.state_dict()["fc.bias"])


def test_missing_and_incompatible_checkpoints_raise_clear_errors(tmp_path: Path) -> None:
    with pytest.raises(CheckpointLoadError, match="does not exist"):
        make_adapter(checkpoint_path=tmp_path / "missing.pth").load()

    bad_path = tmp_path / "incompatible.pth"
    torch.save({"fc.weight": torch.zeros((2, 2))}, bad_path)
    with pytest.raises(CheckpointLoadError, match="strict checkpoint load failed"):
        make_adapter(checkpoint_path=bad_path).load()


def test_registry_metadata_and_model_runner_integration() -> None:
    adapter = create_model_adapter(backend="torchvision", architecture="resnet18", num_classes=3)
    model = adapter.load()

    assert adapter.metadata.to_dict() == {
        "framework": "pytorch",
        "backend": "torchvision",
        "architecture": "resnet18",
        "num_classes": 3,
        "checkpoint_path": None,
    }
    predictions = ModelRunner().predict(model, torch.zeros((2, 3, 32, 32)))
    assert predictions.shape == (2,)
