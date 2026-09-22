class DomainError(ValueError):
    """Base error for violations of domain rules."""


class InvalidBibliographicRecordError(DomainError):
    """Raised when an issue or bibliographic record is invalid."""
