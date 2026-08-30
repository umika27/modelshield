from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from model_adapters import TorchvisionModelAdapter
from training import TrainingConfig, resolve_device, save_checkpoint, seed_everything, train_one_epoch, write_manifest


def test_tiny_training_checkpoint_metadata_and_manifest(tmp_path: Path) -> None:
    config = TrainingConfig(run_name="tiny", epochs=1, batch_size=2, output_dir=tmp_path)
    seed_everything(7)
    model = nn.Sequential(nn.Flatten(), nn.Linear(12, 10))
    before = model[1].weight.detach().clone()
    loader = DataLoader(TensorDataset(torch.rand(4, 3, 2, 2), torch.tensor([0, 1, 2, 3])), batch_size=2, shuffle=False)
    metrics = train_one_epoch(model, loader, torch.optim.SGD(model.parameters(), lr=0.1), torch.device("cpu"))
    checkpoint = tmp_path / "reference.pth"; save_checkpoint(checkpoint, model, config, 1, metrics)
    loaded = torch.load(checkpoint, weights_only=True)
    assert loaded["metadata"]["architecture"] == "resnet18"
    assert loaded["metadata"]["num_classes"] == 10
    assert loaded["metadata"]["class_names"][0] == "airplane"
    assert torch.isfinite(torch.tensor(metrics["loss"])) and not torch.equal(before, model[1].weight)
    write_manifest(tmp_path / "manifest.json", {"baseline": str(checkpoint)})
    assert (tmp_path / "manifest.json").exists()
    assert resolve_device("auto").type in {"cpu", "mps", "cuda"}


def test_reference_checkpoint_metadata_is_exposed_by_adapter(tmp_path: Path) -> None:
    adapter = TorchvisionModelAdapter(architecture="resnet18", num_classes=10)
    path = tmp_path / "model.pth"
    torch.save({"model_state_dict": adapter.load().state_dict(), "metadata": {"class_names": [str(i) for i in range(10)]}}, path)
    loaded = TorchvisionModelAdapter(architecture="resnet18", num_classes=10, checkpoint_path=path)
    loaded.load()
    assert loaded.class_names == tuple(str(i) for i in range(10))
