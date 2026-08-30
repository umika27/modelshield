"""Adapters that connect stable ModelShield subsystems without changing them."""

from .contracts import VerifiedFailureArtifact
from .failure_memory_adapter import FailureMemoryAdapter

__all__ = ["FailureMemoryAdapter", "VerifiedFailureArtifact"]
