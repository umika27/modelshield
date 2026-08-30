"""Explicit serializable configuration for reference model training."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class TrainingConfig:
    run_name: str
    architecture: str = "resnet18"
    dataset: str = "cifar10"
    num_classes: int = 10
    epochs: int = 1
    batch_size: int = 64
    learning_rate: float = 0.01
    weight_decay: float = 0.0001
    optimizer: str = "sgd"
    seed: int = 42
    device: str = "auto"
    augmentation: bool = True
    output_dir: Path = Path("artifacts/models")
    max_train_samples: int | None = None
    max_test_samples: int | None = None
    def __post_init__(self) -> None:
        if self.architecture != "resnet18" or self.dataset != "cifar10": raise ValueError("reference training supports CIFAR-10 ResNet18 only")
        if self.num_classes != 10 or self.epochs <= 0 or self.batch_size <= 0 or self.learning_rate <= 0 or self.weight_decay < 0: raise ValueError("invalid training configuration")
    def to_dict(self) -> dict[str, Any]:
        data = asdict(self); data["output_dir"] = str(self.output_dir); return data
