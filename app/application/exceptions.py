class ApplicationError(RuntimeError):
    """Base error for application workflows."""


class EmptyIssueError(ApplicationError):
    """Raised when an issue contains no bibliographic records."""


class IssueNotFoundError(ApplicationError):
    """Raised when a requested issue is absent from the catalog."""
