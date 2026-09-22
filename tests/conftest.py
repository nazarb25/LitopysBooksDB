from collections.abc import Callable
from pathlib import Path

import pytest

from app.application.dto.issue_import import ExtractedIssueDTO
from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.application.use_cases.issues.import_issue import ImportIssueUseCase
from app.domain.entities import BibliographicDetails, Book, Issue
from app.infrastructure.database.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories.book_catalog_read_repository import (
    SqlAlchemyBookCatalogReadRepository,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ISSUE = Issue("https://ukrbook.net/litopys/Knigki/2026/L_k_16_2026.pdf", 2026, 16)


class FakeExtractor:
    def extract(self, issue: Issue, pdf: bytes) -> ExtractedIssueDTO:
        return ExtractedIssueDTO(
            books=(
                Book(
                    issue.url,
                    7701,
                    "Темна вежа",
                    "Кінг С. Темна вежа / Стівен Кінг. — Харків : КСД, 2025.",
                    5,
                    "Кінг С.",
                    "978-617-123-456-7",
                    2025,
                    BibliographicDetails(
                        responsibility="Стівен Кінг ; пер. з англ. І. Перекладача",
                        publication_place="Харків",
                        publisher="КСД",
                        physical_description="500 с. ; 21 см",
                        print_run=3000,
                        catalog_number="2026-07701",
                        udc="821.111",
                        original_title="The Dark Tower",
                        original_isbn="978-1-234-56789-0",
                        translators="І. Перекладача",
                        editors="Р. Редактора",
                        illustrators="Х. Художника",
                    ),
                ),
            ),
            month=8,
        )

    def extract_month(self, issue: Issue, pdf: bytes) -> int | None:
        return 8


@pytest.fixture
def use_cases(
    tmp_path: Path,
) -> tuple[
    ImportIssueUseCase,
    SearchBooksUseCase,
    Callable[[], SqlAlchemyUnitOfWork],
]:
    engine = create_database_engine(tmp_path / "books.db")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)
    importer = ImportIssueUseCase(FakeExtractor(), uow_factory)
    search = SearchBooksUseCase(SqlAlchemyBookCatalogReadRepository(session_factory))
    return importer, search, uow_factory
