from dataclasses import dataclass

from sqlalchemy import Engine

from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.infrastructure.config.settings import Settings
from app.infrastructure.database.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.database.repositories.book_catalog_read_repository import (
    SqlAlchemyBookCatalogReadRepository,
)


@dataclass(slots=True)
class WebContainer:
    settings: Settings
    engine: Engine
    search_books: SearchBooksUseCase

    def close(self) -> None:
        self.engine.dispose()


def create_web_container(settings: Settings | None = None) -> WebContainer:
    settings = settings or Settings()
    engine = create_database_engine(
        settings.database_path,
        read_only=settings.database_read_only,
    )
    session_factory = create_session_factory(engine)
    repository = SqlAlchemyBookCatalogReadRepository(session_factory)
    return WebContainer(
        settings=settings,
        engine=engine,
        search_books=SearchBooksUseCase(repository),
    )
