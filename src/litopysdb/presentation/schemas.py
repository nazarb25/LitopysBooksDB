from pydantic import BaseModel, ConfigDict, Field

from litopysdb.domain.models import Book


class BibliographicDetailsRead(BaseModel):
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


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record_number: int
    author: str | None
    title: str
    description: str
    isbn: str | None
    publication_year: int | None
    issue_year: int | None
    issue_number: int | None
    issue_month: int | None
    source_page: int
    issue_url: str
    pdf_url: str
    details: BibliographicDetailsRead

    @classmethod
    def from_book(cls, book: Book) -> BookRead:
        return cls(
            record_number=book.record_number,
            author=book.author,
            title=book.title,
            description=book.description,
            isbn=book.isbn,
            publication_year=book.publication_year,
            issue_year=book.issue_year,
            issue_number=book.issue_number,
            issue_month=book.issue_month,
            source_page=book.source_page,
            issue_url=book.issue_url,
            pdf_url=f"{book.issue_url}#page={book.source_page}",
            details=BibliographicDetailsRead.model_validate(book.details, from_attributes=True),
        )


class SearchResponse(BaseModel):
    items: list[BookRead]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)
    page: int = Field(ge=1)
    pages: int = Field(ge=0)
