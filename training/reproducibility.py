"""Deterministic training-process setup."""
import random
import numpy as np
import torch

def seed_everything(seed: int) -> None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

def resolve_device(requested: str = "auto") -> torch.device:
    if requested == "auto":
        if torch.cuda.is_available(): return torch.device("cuda")
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available(): return torch.device("mps")
        return torch.device("cpu")
    return torch.device(requested)
