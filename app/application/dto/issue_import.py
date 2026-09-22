from dataclasses import dataclass

from app.domain.entities import Book, Issue


@dataclass(frozen=True, slots=True)
class ExtractedIssueDTO:
    books: tuple[Book, ...]
    month: int | None


@dataclass(frozen=True, slots=True)
class ImportIssueResultDTO:
    issue: Issue
    books: int
    skipped: bool


@dataclass(frozen=True, slots=True)
class SyncIssueOutcomeDTO:
    issue: Issue
    result: ImportIssueResultDTO | None
    error: str | None


@dataclass(frozen=True, slots=True)
class BookDetailsSourceDTO:
    id: int
    description: str


@dataclass(frozen=True, slots=True)
class ParsedBookDetailsDTO:
    id: int
    isbn: str | None
    responsibility: str | None
    publication_place: str | None
    publisher: str | None
    physical_description: str | None
    print_run: int | None
    catalog_number: str | None
    udc: str | None
    original_title: str | None
    original_isbn: str | None
    translators: str | None
    editors: str | None
    illustrators: str | None
