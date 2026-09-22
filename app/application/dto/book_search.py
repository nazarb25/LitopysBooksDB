from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SearchBooksQuery:
    author: str | None = None
    text: str | None = None
    year: int | None = None
    issue_year: int | None = None
    issue_month: int | None = None
    issue_number: int | None = None
    publisher: str | None = None
    publication_place: str | None = None
    translator: str | None = None
    editor: str | None = None
    illustrator: str | None = None
    original_title: str | None = None
    isbn: str | None = None
    original_isbn: str | None = None
    udc: str | None = None
    catalog_number: str | None = None
    responsibility: str | None = None
    physical_description: str | None = None
    print_run_min: int | None = None
    print_run_max: int | None = None
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        criteria = (
            self.author,
            self.text,
            self.year,
            self.issue_year,
            self.issue_month,
            self.issue_number,
            self.publisher,
            self.publication_place,
            self.translator,
            self.editor,
            self.illustrator,
            self.original_title,
            self.isbn,
            self.original_isbn,
            self.udc,
            self.catalog_number,
            self.responsibility,
            self.physical_description,
            self.print_run_min,
            self.print_run_max,
        )
        if not any(value is not None and value != "" for value in criteria):
            raise ValueError("Specify search text or at least one filter")
        if self.issue_year is not None and not 1924 <= self.issue_year <= 2100:
            raise ValueError("Invalid issue year")
        if self.issue_month is not None and not 1 <= self.issue_month <= 12:
            raise ValueError("Issue month must be between 1 and 12")
        if self.issue_number is not None and self.issue_number < 1:
            raise ValueError("Issue number must be positive")
        if self.print_run_min is not None and self.print_run_min < 0:
            raise ValueError("Minimum print run must not be negative")
        if self.print_run_max is not None and self.print_run_max < 0:
            raise ValueError("Maximum print run must not be negative")
        if (
            self.print_run_min is not None
            and self.print_run_max is not None
            and self.print_run_min > self.print_run_max
        ):
            raise ValueError("Minimum print run must not exceed maximum print run")
        if not 1 <= self.limit <= 500 or self.offset < 0:
            raise ValueError("Invalid limit or offset")


@dataclass(frozen=True, slots=True)
class BibliographicDetailsDTO:
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
class BookCatalogItemDTO:
    issue_url: str
    record_number: int
    title: str
    description: str
    source_page: int
    author: str | None
    isbn: str | None
    publication_year: int | None
    issue_year: int
    issue_number: int
    issue_month: int | None
    details: BibliographicDetailsDTO = field(default_factory=BibliographicDetailsDTO)


@dataclass(frozen=True, slots=True)
class BookSearchPageDTO:
    items: tuple[BookCatalogItemDTO, ...]
    total: int
    limit: int
    offset: int

    @property
    def page(self) -> int:
        return self.offset // self.limit + 1

    @property
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit if self.total else 0
