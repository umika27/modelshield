from pathlib import Path

from PIL import Image
import pytest
import torch

from core.runner import ModelRunner
from dataset_adapters import ImageFolderAdapter
from model_adapters import (
    ModelDatasetCompatibilityError,
    TorchvisionModelAdapter,
    validate_model_dataset_compatibility,
)


@pytest.mark.parametrize("architecture", ["resnet18", "resnet50", "mobilenet_v3_small", "efficientnet_b0"])
def test_every_supported_adapter_exposes_valid_preprocessing(architecture: str) -> None:
    adapter = TorchvisionModelAdapter(architecture=architecture, num_classes=2)
    spec = adapter.preprocessing
    assert spec.input_size == (224, 224)
    assert spec.mean == (0.485, 0.456, 0.406)
    assert spec.std == (0.229, 0.224, 0.225)


def test_preprocess_resizes_normalizes_and_does_not_mutate() -> None:
    adapter = TorchvisionModelAdapter(architecture="resnet18", num_classes=2)
    images = torch.full((2, 3, 12, 16), 0.5, dtype=torch.float32)
    original = images.clone()

    processed = adapter.preprocess(images)

    assert processed.shape == (2, 3, 224, 224)
    assert processed.dtype == torch.float32
    assert torch.equal(images, original)
    assert torch.isfinite(processed).all()


@pytest.mark.parametrize(
    "images",
    [
        torch.zeros((3, 8, 8), dtype=torch.float32),
        torch.zeros((1, 1, 8, 8), dtype=torch.float32),
        torch.zeros((1, 3, 8, 8), dtype=torch.float64),
        torch.full((1, 3, 8, 8), float("nan"), dtype=torch.float32),
        torch.full((1, 3, 8, 8), 1.1, dtype=torch.float32),
    ],
)
def test_preprocess_rejects_invalid_canonical_input(images: torch.Tensor) -> None:
    with pytest.raises((TypeError, ValueError), match="images"):
        TorchvisionModelAdapter(architecture="resnet18", num_classes=2).preprocess(images)


def make_imagefolder(root: Path) -> Path:
    for class_name, color in {"cat": (10, 20, 30), "dog": (200, 210, 220)}.items():
        directory = root / class_name
        directory.mkdir(parents=True)
        Image.new("RGB", (16, 12), color=color).save(directory / "one.png")
    return root


def test_real_imagefolder_to_preprocessing_to_modelrunner_integration(tmp_path: Path) -> None:
    dataset_adapter = ImageFolderAdapter(root=make_imagefolder(tmp_path / "images"))
    dataset_adapter.load()
    canonical_images, _ = next(iter(dataset_adapter.create_dataloader(batch_size=2)))
    adapter = TorchvisionModelAdapter(architecture="resnet18", num_classes=2)

    validate_model_dataset_compatibility(adapter, dataset_adapter)
    processed = adapter.preprocess(canonical_images)
    model = adapter.load()
    logits = model(processed)
    predictions = ModelRunner().predict(model, processed)

    assert canonical_images.shape == (2, 3, 12, 16)
    assert canonical_images.dtype == torch.float32
    assert logits.shape == (2, 2)
    assert predictions.shape == (2,)


def test_model_dataset_class_count_mismatch_is_rejected(tmp_path: Path) -> None:
    dataset_adapter = ImageFolderAdapter(root=make_imagefolder(tmp_path / "images"))
    dataset_adapter.load()
    model_adapter = TorchvisionModelAdapter(architecture="resnet18", num_classes=3)

    with pytest.raises(ModelDatasetCompatibilityError, match="expects 3 classes"):
        validate_model_dataset_compatibility(model_adapter, dataset_adapter)
