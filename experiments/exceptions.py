"""Failures specific to real comparison execution."""


class ExperimentError(Exception):
    """Base experiment error."""


class ExperimentCompatibilityError(ExperimentError):
    """Raised when models and dataset cannot be safely compared."""


class ExperimentExecutionError(ExperimentError):
    """Raised when a loaded model produces invalid comparison evidence."""
