from typing import Protocol

from app.domain.entities import Issue


class IssueDownloader(Protocol):
    def download(self, issue: Issue) -> bytes: ...
