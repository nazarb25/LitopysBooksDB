from app.application.dto.book_search import BookSearchPageDTO, SearchBooksQuery
from app.application.interfaces.repositories.book_catalog_read_repository import (
    BookCatalogReadRepository,
)


class SearchBooksUseCase:
    def __init__(self, repository: BookCatalogReadRepository) -> None:
        self._repository = repository

    def execute(self, query: SearchBooksQuery) -> BookSearchPageDTO:
        return self._repository.search(query)
