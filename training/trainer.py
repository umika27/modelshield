"""Small supervised loop used only to create legitimate reference checkpoints."""
from __future__ import annotations
import torch
from torch import nn
from torch.utils.data import DataLoader

def train_one_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> dict[str, float]:
    model.train(); loss_sum = correct = total = 0; criterion = nn.CrossEntropyLoss()
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad(); logits = model(images); loss = criterion(logits, labels); loss.backward(); optimizer.step()
        loss_sum += float(loss.item()) * labels.numel(); correct += int((logits.argmax(1) == labels).sum()); total += labels.numel()
    return {"loss": loss_sum / total, "accuracy": correct / total}
