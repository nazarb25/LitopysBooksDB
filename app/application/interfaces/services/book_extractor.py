from typing import Protocol

from app.application.dto.issue_import import ExtractedIssueDTO
from app.domain.entities import Issue


class BookExtractor(Protocol):
    def extract(self, issue: Issue, pdf: bytes) -> ExtractedIssueDTO: ...

    def extract_month(self, issue: Issue, pdf: bytes) -> int | None: ...
