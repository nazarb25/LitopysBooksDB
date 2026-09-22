from collections.abc import Sequence
from typing import Protocol, Self

from litopysdb.domain.models import Book, Issue, ParsedIssue


class IssueCatalog(Protocol):
    def list_issues(self) -> Sequence[Issue]: ...


class IssueDownloader(Protocol):
    def download(self, issue: Issue) -> bytes: ...


class PdfArchive(Protocol):
    def save(self, issue: Issue, pdf: bytes) -> None: ...
    def load(self, issue: Issue) -> bytes | None: ...


class BookExtractor(Protocol):
    def extract(self, issue: Issue, pdf: bytes) -> ParsedIssue: ...
    def extract_month(self, issue: Issue, pdf: bytes) -> int | None: ...


class BookRepository(Protocol):
    def has_issue(self, issue: Issue) -> bool: ...
    def latest_issue(self) -> Issue | None: ...
    def is_current(self, issue: Issue, digest: str) -> bool: ...
    def replace_issue(
        self, issue: Issue, digest: str, month: int | None, books: Sequence[Book]
    ) -> None: ...
    def issues_missing_month(self) -> Sequence[Issue]: ...
    def set_issue_month(self, issue: Issue, month: int) -> None: ...
    def backfill_details(self, batch_size: int = 5000) -> int: ...
    def search(self, query: SearchQuery) -> Sequence[Book]: ...
    def count_search(self, query: SearchQuery) -> int: ...
    def count_issues(self) -> int: ...
    def count_books(self) -> int: ...


class UnitOfWork(Protocol):
    books: BookRepository

    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...
    def commit(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...


class SearchQuery:
    def __init__(
        self,
        *,
        author: str | None = None,
        text: str | None = None,
        year: int | None = None,
        issue_year: int | None = None,
        issue_month: int | None = None,
        issue_number: int | None = None,
        publisher: str | None = None,
        publication_place: str | None = None,
        translator: str | None = None,
        editor: str | None = None,
        illustrator: str | None = None,
        original_title: str | None = None,
        isbn: str | None = None,
        original_isbn: str | None = None,
        udc: str | None = None,
        catalog_number: str | None = None,
        responsibility: str | None = None,
        physical_description: str | None = None,
        print_run_min: int | None = None,
        print_run_max: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        criteria = (
            author,
            text,
            year,
            issue_year,
            issue_month,
            issue_number,
            publisher,
            publication_place,
            translator,
            editor,
            illustrator,
            original_title,
            isbn,
            original_isbn,
            udc,
            catalog_number,
            responsibility,
            physical_description,
            print_run_min,
            print_run_max,
        )
        if not any(value is not None and value != "" for value in criteria):
            raise ValueError("Specify search text or at least one filter")
        if issue_year is not None and not 1924 <= issue_year <= 2100:
            raise ValueError("Invalid issue year")
        if issue_month is not None and not 1 <= issue_month <= 12:
            raise ValueError("Issue month must be between 1 and 12")
        if issue_number is not None and issue_number < 1:
            raise ValueError("Issue number must be positive")
        if print_run_min is not None and print_run_min < 0:
            raise ValueError("Minimum print run must not be negative")
        if print_run_max is not None and print_run_max < 0:
            raise ValueError("Maximum print run must not be negative")
        if (
            print_run_min is not None
            and print_run_max is not None
            and print_run_min > print_run_max
        ):
            raise ValueError("Minimum print run must not exceed maximum print run")
        if not 1 <= limit <= 500 or offset < 0:
            raise ValueError("Invalid limit or offset")
        self.author = author
        self.text = text
        self.year = year
        self.issue_year = issue_year
        self.issue_month = issue_month
        self.issue_number = issue_number
        self.publisher = publisher
        self.publication_place = publication_place
        self.translator = translator
        self.editor = editor
        self.illustrator = illustrator
        self.original_title = original_title
        self.isbn = isbn
        self.original_isbn = original_isbn
        self.udc = udc
        self.catalog_number = catalog_number
        self.responsibility = responsibility
        self.physical_description = physical_description
        self.print_run_min = print_run_min
        self.print_run_max = print_run_max
        self.limit = limit
        self.offset = offset
