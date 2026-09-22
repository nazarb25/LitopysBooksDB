from collections.abc import Sequence
from typing import Protocol

from app.application.dto.issue_import import (
    BookDetailsSourceDTO,
    ParsedBookDetailsDTO,
)
from app.domain.entities import Book, Issue


class IssueRepository(Protocol):
    def has(self, issue: Issue) -> bool: ...

    def latest(self) -> Issue | None: ...

    def is_current(self, issue: Issue, digest: str) -> bool: ...

    def replace(
        self,
        issue: Issue,
        digest: str,
        month: int | None,
        books: Sequence[Book],
    ) -> None: ...

    def list_missing_month(self) -> Sequence[Issue]: ...

    def set_month(self, issue: Issue, month: int) -> None: ...

    def list_book_details_sources(
        self,
        *,
        after_id: int,
        limit: int,
    ) -> Sequence[BookDetailsSourceDTO]: ...

    def update_book_details(self, records: Sequence[ParsedBookDetailsDTO]) -> None: ...
