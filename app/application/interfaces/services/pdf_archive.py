from typing import Protocol

from app.domain.entities import Issue


class PdfArchive(Protocol):
    def save(self, issue: Issue, pdf: bytes) -> None: ...

    def load(self, issue: Issue) -> bytes | None: ...
