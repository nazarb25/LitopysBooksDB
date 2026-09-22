from collections.abc import Sequence
from typing import Protocol

from app.domain.entities import Issue


class IssueCatalog(Protocol):
    def list_issues(self) -> Sequence[Issue]: ...
