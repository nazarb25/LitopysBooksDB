from dataclasses import dataclass, field

from app.domain.entities.bibliographic_details import BibliographicDetails
from app.domain.exceptions import InvalidBibliographicRecordError


@dataclass(frozen=True, slots=True)
class Book:
    issue_url: str
    record_number: int
    title: str
    description: str
    source_page: int
    author: str | None = None
    isbn: str | None = None
    publication_year: int | None = None
    details: BibliographicDetails = field(default_factory=BibliographicDetails)

    def __post_init__(self) -> None:
        if self.record_number < 1 or self.source_page < 1:
            raise InvalidBibliographicRecordError("Record number and source page must be positive")
        if not self.title.strip() or not self.description.strip():
            raise InvalidBibliographicRecordError("Title and description must not be empty")
        if self.publication_year is not None and not 1400 <= self.publication_year <= 2100:
            raise InvalidBibliographicRecordError("Publication year is out of range")
