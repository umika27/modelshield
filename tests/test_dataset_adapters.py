from pathlib import Path

from PIL import Image
import pytest
import torch

from dataset_adapters import (
    CIFAR10Adapter,
    DatasetLoadError,
    ImageFolderAdapter,
    create_dataset_adapter,
    supported_dataset_types,
    validate_canonical_batch,
)


def make_imagefolder(root: Path, *, varied_sizes: bool = False) -> Path:
    for class_name, values in {"cat": [20, 40, 60], "dog": [160, 180, 200]}.items():
        class_dir = root / class_name
        class_dir.mkdir(parents=True)
        for index, value in enumerate(values):
            size = (8 + index, 10 + index) if varied_sizes else (10, 10)
            Image.new("RGB", size, color=(value, value, value)).save(class_dir / f"{index}.png")
    return root


def test_imagefolder_loads_canonical_samples_and_metadata(tmp_path: Path) -> None:
    adapter = ImageFolderAdapter(root=make_imagefolder(tmp_path / "images"), split="test")
    dataset = adapter.load()
    image, label = dataset[0]

    assert isinstance(image, torch.Tensor)
    assert image.dtype == torch.float32
    assert image.shape == (3, 10, 10)
    assert 0 <= image.min() and image.max() <= 1
    assert label == 0
    assert adapter.metadata.class_names == ("cat", "dog")
    assert adapter.metadata.class_to_idx == {"cat": 0, "dog": 1}
    assert adapter.metadata.num_samples == 6


def test_imagefolder_loader_batches_and_resizes(tmp_path: Path) -> None:
    adapter = ImageFolderAdapter(root=make_imagefolder(tmp_path / "images", varied_sizes=True), image_size=(12, 14))
    adapter.load()
    images, labels = next(iter(adapter.create_dataloader(batch_size=2)))

    assert images.shape == (2, 3, 12, 14)
    assert labels.dtype == torch.int64
    assert validate_canonical_batch(images) is images


def test_imagefolder_errors_are_clear(tmp_path: Path) -> None:
    with pytest.raises(DatasetLoadError, match="does not exist"):
        ImageFolderAdapter(root=tmp_path / "missing").load()
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(DatasetLoadError, match="no class folders"):
        ImageFolderAdapter(root=empty).load()
    malformed = tmp_path / "malformed"
    (malformed / "cat").mkdir(parents=True)
    with pytest.raises(DatasetLoadError, match="unable to load ImageFolder"):
        ImageFolderAdapter(root=malformed).load()


def test_dataloader_order_is_deterministic_with_seed(tmp_path: Path) -> None:
    adapter = ImageFolderAdapter(root=make_imagefolder(tmp_path / "images"))
    adapter.load()

    def order(seed: int | None, shuffle: bool) -> list[int]:
        return [int(image[0, 0, 0].item() * 255) for images, _ in [next(iter(adapter.create_dataloader(batch_size=6, shuffle=shuffle, seed=seed)))] for image in images]

    assert order(None, False) == order(None, False)
    assert order(7, True) == order(7, True)
    assert order(7, True) != order(8, True)


def test_dataset_registry_and_cifar_class_order() -> None:
    assert supported_dataset_types() == ("cifar10", "imagefolder")
    assert CIFAR10Adapter.CLASS_NAMES == (
        "airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"
    )
    adapter = create_dataset_adapter(dataset_type="cifar10", root="/tmp/cifar")
    assert isinstance(adapter, CIFAR10Adapter)
    assert adapter.download is False


def test_missing_cifar_is_offline_by_default(tmp_path: Path) -> None:
    with pytest.raises(DatasetLoadError, match="download=True"):
        CIFAR10Adapter(root=tmp_path / "no-data").load()
