from dataclasses import dataclass
from urllib.parse import urlparse

from app.domain.exceptions import InvalidBibliographicRecordError


@dataclass(frozen=True, slots=True)
class Issue:
    url: str
    year: int
    number: int

    def __post_init__(self) -> None:
        if urlparse(self.url).scheme not in {"http", "https"} or not self.url.lower().endswith(
            ".pdf"
        ):
            raise InvalidBibliographicRecordError("Issue must have an HTTP PDF URL")
        if self.year < 1924 or self.number < 1:
            raise InvalidBibliographicRecordError("Invalid issue year or number")
