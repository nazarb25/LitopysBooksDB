from collections.abc import Sequence
from dataclasses import dataclass, field
from urllib.parse import urlparse


class InvalidBibliographicRecord(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Issue:
    url: str
    year: int
    number: int

    def __post_init__(self) -> None:
        if urlparse(self.url).scheme not in {"http", "https"} or not self.url.lower().endswith(
            ".pdf"
        ):
            raise InvalidBibliographicRecord("Issue must have an HTTP PDF URL")
        if self.year < 1924 or self.number < 1:
            raise InvalidBibliographicRecord("Invalid issue year or number")


@dataclass(frozen=True, slots=True)
class BibliographicDetails:
    responsibility: str | None = None
    publication_place: str | None = None
    publisher: str | None = None
    physical_description: str | None = None
    print_run: int | None = None
    catalog_number: str | None = None
    udc: str | None = None
    original_title: str | None = None
    original_isbn: str | None = None
    translators: str | None = None
    editors: str | None = None
    illustrators: str | None = None


@dataclass(frozen=True, slots=True)
class Book:
    issue_url: str
    record_number: int
    title: str
    description: str
    source_page: int
    author: str | None = None
    isbn: str | None = None
    publication_year: int | None = None
    issue_year: int | None = None
    issue_number: int | None = None
    issue_month: int | None = None
    details: BibliographicDetails = field(default_factory=BibliographicDetails)

    def __post_init__(self) -> None:
        if self.record_number < 1 or self.source_page < 1:
            raise InvalidBibliographicRecord("Record number and source page must be positive")
        if not self.title.strip() or not self.description.strip():
            raise InvalidBibliographicRecord("Title and description must not be empty")
        if self.publication_year is not None and not 1400 <= self.publication_year <= 2100:
            raise InvalidBibliographicRecord("Publication year is out of range")


@dataclass(frozen=True, slots=True)
class ParsedIssue:
    books: Sequence[Book]
    month: int | None
