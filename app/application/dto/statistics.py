from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CatalogStatisticsDTO:
    issues: int
    books: int
