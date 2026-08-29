"""Dataset adapter failures with actionable messages."""


class DatasetAdapterError(Exception):
    """Base exception for dataset adapter operations."""


class DatasetLoadError(DatasetAdapterError):
    """Raised when a local dataset cannot be loaded."""


class DatasetValidationError(DatasetAdapterError):
    """Raised when data does not meet ModelShield's canonical image contract."""


class UnsupportedDatasetTypeError(DatasetAdapterError):
    """Raised when the dataset registry does not support a requested type."""
