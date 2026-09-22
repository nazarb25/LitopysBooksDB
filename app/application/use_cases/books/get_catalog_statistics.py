from app.application.dto.statistics import CatalogStatisticsDTO
from app.application.interfaces.repositories.book_catalog_read_repository import (
    BookCatalogReadRepository,
)


class GetCatalogStatisticsUseCase:
    def __init__(self, repository: BookCatalogReadRepository) -> None:
        self._repository = repository

    def execute(self) -> CatalogStatisticsDTO:
        return self._repository.get_statistics()
