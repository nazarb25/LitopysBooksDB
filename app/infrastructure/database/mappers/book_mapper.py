import re

from app.application.dto.book_search import (
    BibliographicDetailsDTO,
    BookCatalogItemDTO,
)
from app.domain.entities import Book
from app.infrastructure.database.models import BookModel, IssueModel


class BookMapper:
    @staticmethod
    def search_key(value: str) -> str:
        return " ".join(re.findall(r"\w+", value.casefold()))

    @classmethod
    def author_key(cls, value: str | None) -> str | None:
        if not value:
            return None
        tokens = cls.search_key(value).split()
        if len(tokens) >= 2:
            return " ".join(tokens + [tokens[-1], tokens[0][0]])
        return " ".join(tokens)

    @classmethod
    def to_model(cls, book: Book) -> BookModel:
        return BookModel(
            record_number=book.record_number,
            title=book.title,
            title_key=cls.search_key(book.title),
            description=book.description,
            source_page=book.source_page,
            author=book.author,
            author_key=cls.author_key(book.author),
            isbn=book.isbn,
            publication_year=book.publication_year,
            responsibility=book.details.responsibility,
            publication_place=book.details.publication_place,
            publisher=book.details.publisher,
            physical_description=book.details.physical_description,
            print_run=book.details.print_run,
            catalog_number=book.details.catalog_number,
            udc=book.details.udc,
            original_title=book.details.original_title,
            original_isbn=book.details.original_isbn,
            translators=book.details.translators,
            editors=book.details.editors,
            illustrators=book.details.illustrators,
        )

    @staticmethod
    def to_dto(book: BookModel, issue: IssueModel) -> BookCatalogItemDTO:
        return BookCatalogItemDTO(
            issue_url=issue.url,
            record_number=book.record_number,
            title=book.title,
            description=book.description,
            source_page=book.source_page,
            author=book.author,
            isbn=book.isbn,
            publication_year=book.publication_year,
            issue_year=issue.year,
            issue_number=issue.number,
            issue_month=issue.month,
            details=BibliographicDetailsDTO(
                responsibility=book.responsibility,
                publication_place=book.publication_place,
                publisher=book.publisher,
                physical_description=book.physical_description,
                print_run=book.print_run,
                catalog_number=book.catalog_number,
                udc=book.udc,
                original_title=book.original_title,
                original_isbn=book.original_isbn,
                translators=book.translators,
                editors=book.editors,
                illustrators=book.illustrators,
            ),
        )
