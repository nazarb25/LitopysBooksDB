from typing import Protocol

from app.application.dto.book_search import BookSearchPageDTO, SearchBooksQuery
from app.application.dto.statistics import CatalogStatisticsDTO


class BookCatalogReadRepository(Protocol):
    def search(self, query: SearchBooksQuery) -> BookSearchPageDTO: ...

    def get_statistics(self) -> CatalogStatisticsDTO: ...
