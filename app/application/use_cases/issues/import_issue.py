from hashlib import sha256

from app.application.dto.issue_import import ImportIssueResultDTO
from app.application.exceptions import EmptyIssueError
from app.application.interfaces.services.book_extractor import BookExtractor
from app.application.interfaces.unit_of_work import UnitOfWorkFactory
from app.domain.entities import Issue


class ImportIssueUseCase:
    PARSER_VERSION = b"litopysdb-parser-v7"

    def __init__(self, extractor: BookExtractor, uow_factory: UnitOfWorkFactory) -> None:
        self._extractor = extractor
        self._uow_factory = uow_factory

    def execute(self, issue: Issue, pdf: bytes) -> ImportIssueResultDTO:
        digest = sha256(pdf + self.PARSER_VERSION).hexdigest()
        with self._uow_factory() as uow:
            if uow.issues.is_current(issue, digest):
                return ImportIssueResultDTO(issue=issue, books=0, skipped=True)

        extracted = self._extractor.extract(issue, pdf)
        if not extracted.books:
            raise EmptyIssueError(f"No bibliographic records found in {issue.url}")

        with self._uow_factory() as uow:
            uow.issues.replace(issue, digest, extracted.month, extracted.books)
            uow.commit()
        return ImportIssueResultDTO(issue=issue, books=len(extracted.books), skipped=False)

    def has_issue(self, issue: Issue) -> bool:
        with self._uow_factory() as uow:
            return uow.issues.has(issue)

    def latest_issue(self) -> Issue | None:
        with self._uow_factory() as uow:
            return uow.issues.latest()
