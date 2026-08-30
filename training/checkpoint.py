"""Durable checkpoint and manifest serialization."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import torch
from torch import nn
from .config import TrainingConfig

CIFAR10_CLASSES = ("airplane","automobile","bird","cat","deer","dog","frog","horse","ship","truck")
def save_checkpoint(path: Path, model: nn.Module, config: TrainingConfig, epoch: int, metrics: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "metadata": {"schema_version":"1.0","architecture":config.architecture,"num_classes":config.num_classes,"class_names":list(CIFAR10_CLASSES),"dataset_name":"cifar10","training_run_name":config.run_name,"seed":config.seed,"training_configuration":config.to_dict(),"epoch":epoch,"final_training_metrics":metrics,"timestamp":datetime.now(timezone.utc).isoformat()}}, path)
def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload, indent=2, sort_keys=True))
