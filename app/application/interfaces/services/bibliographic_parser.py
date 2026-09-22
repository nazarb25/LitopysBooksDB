from typing import Protocol

from app.domain.entities import BibliographicDetails


class BibliographicParser(Protocol):
    def parse(self, description: str) -> BibliographicDetails: ...

    def primary_isbn(self, description: str) -> str | None: ...
