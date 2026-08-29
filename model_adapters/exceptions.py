"""Clear adapter errors suitable for callers and CLI layers."""


class ModelAdapterError(Exception):
    """Base exception for model adapter failures."""


class UnsupportedArchitectureError(ModelAdapterError):
    """Raised when an adapter does not support an architecture name."""


class UnsupportedBackendError(ModelAdapterError):
    """Raised when the adapter registry does not support a backend."""


class CheckpointLoadError(ModelAdapterError):
    """Raised when a checkpoint cannot be loaded into the requested model."""


class InvalidCheckpointError(CheckpointLoadError):
    """Raised when checkpoint content is not a supported state-dict format."""


class ModelDatasetCompatibilityError(ModelAdapterError):
    """Raised when a model's output classes do not match a dataset."""
