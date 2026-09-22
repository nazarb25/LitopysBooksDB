from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.use_cases.books.backfill_book_details import (
    BackfillBookDetailsUseCase,
)
from app.application.use_cases.books.get_catalog_statistics import (
    GetCatalogStatisticsUseCase,
)
from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.application.use_cases.issues.backfill_issue_months import (
    BackfillIssueMonthsUseCase,
)
from app.application.use_cases.issues.import_issue import ImportIssueUseCase
from app.application.use_cases.issues.sync_catalog import SyncCatalogUseCase
from app.infrastructure.clients.book_chamber_client import BookChamberClient
from app.infrastructure.config.settings import Settings
from app.infrastructure.database.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.database.repositories.book_catalog_read_repository import (
    SqlAlchemyBookCatalogReadRepository,
)
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.parsers.bibliography_parser import RegexBibliographicParser
from app.infrastructure.parsers.pdf_book_extractor import PyMuPdfBookExtractor
from app.infrastructure.storage.local_pdf_archive import LocalPdfArchive


@dataclass(slots=True)
class Container:
    settings: Settings
    session_factory: sessionmaker[Session]
    uow_factory: Callable[[], UnitOfWork]
    search_books: SearchBooksUseCase
    import_issue: ImportIssueUseCase
    sync_catalog: SyncCatalogUseCase
    backfill_issue_months: BackfillIssueMonthsUseCase
    backfill_book_details: BackfillBookDetailsUseCase
    get_catalog_statistics: GetCatalogStatisticsUseCase
    source: BookChamberClient

    def close(self) -> None:
        self.source.close()


def create_container(settings: Settings | None = None) -> Container:
    settings = settings or Settings()
    engine = create_database_engine(settings.database_path)
    session_factory = create_session_factory(engine)
    uow_factory = lambda: SqlAlchemyUnitOfWork(session_factory)
    read_repository = SqlAlchemyBookCatalogReadRepository(session_factory)
    extractor = PyMuPdfBookExtractor()
    archive = LocalPdfArchive(settings.pdf_directory)
    source = BookChamberClient()
    importer = ImportIssueUseCase(extractor, uow_factory)
    return Container(
        settings=settings,
        session_factory=session_factory,
        uow_factory=uow_factory,
        search_books=SearchBooksUseCase(read_repository),
        import_issue=importer,
        sync_catalog=SyncCatalogUseCase(source, source, archive, importer),
        backfill_issue_months=BackfillIssueMonthsUseCase(
            extractor,
            archive,
            uow_factory,
        ),
        backfill_book_details=BackfillBookDetailsUseCase(
            RegexBibliographicParser(),
            uow_factory,
        ),
        get_catalog_statistics=GetCatalogStatisticsUseCase(read_repository),
        source=source,
    )
