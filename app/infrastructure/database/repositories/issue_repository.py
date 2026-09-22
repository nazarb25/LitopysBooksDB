from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.application.dto.issue_import import (
    BookDetailsSourceDTO,
    ParsedBookDetailsDTO,
)
from app.application.exceptions import IssueNotFoundError
from app.domain.entities import Book, Issue
from app.infrastructure.database.mappers.book_mapper import BookMapper
from app.infrastructure.database.models import BookModel, IssueModel


class SqlAlchemyIssueRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def has(self, issue: Issue) -> bool:
        return self._find_id(issue) is not None

    def latest(self) -> Issue | None:
        model = self._session.scalar(
            select(IssueModel).order_by(IssueModel.year.desc(), IssueModel.number.desc()).limit(1)
        )
        return Issue(model.url, model.year, model.number) if model is not None else None

    def is_current(self, issue: Issue, digest: str) -> bool:
        model = self._find(issue)
        return model is not None and model.sha256 == digest

    def replace(
        self,
        issue: Issue,
        digest: str,
        month: int | None,
        books: Sequence[Book],
    ) -> None:
        model = self._find(issue)
        if model is None:
            model = IssueModel(
                url=issue.url,
                year=issue.year,
                number=issue.number,
                month=month,
                sha256=digest,
            )
            self._session.add(model)
        else:
            model.url = issue.url
            model.sha256 = digest
            model.month = month
            model.books.clear()
            self._session.flush()
        model.books.extend(BookMapper.to_model(book) for book in books)

    def list_missing_month(self) -> Sequence[Issue]:
        models = self._session.scalars(select(IssueModel).where(IssueModel.month.is_(None))).all()
        return tuple(Issue(model.url, model.year, model.number) for model in models)

    def set_month(self, issue: Issue, month: int) -> None:
        model = self._find(issue)
        if model is None:
            raise IssueNotFoundError(f"Issue {issue.year} #{issue.number} is not indexed")
        model.month = month

    def list_book_details_sources(
        self,
        *,
        after_id: int,
        limit: int,
    ) -> Sequence[BookDetailsSourceDTO]:
        rows = self._session.execute(
            select(BookModel.id, BookModel.description)
            .where(BookModel.id > after_id)
            .order_by(BookModel.id)
            .limit(limit)
        ).all()
        return tuple(BookDetailsSourceDTO(id=row.id, description=row.description) for row in rows)

    def update_book_details(self, records: Sequence[ParsedBookDetailsDTO]) -> None:
        for record in records:
            values = {
                field: getattr(record, field)
                for field in ParsedBookDetailsDTO.__dataclass_fields__
                if field != "id"
            }
            if values["isbn"] is None:
                del values["isbn"]
            self._session.execute(
                update(BookModel).where(BookModel.id == record.id).values(**values)
            )

    def _find(self, issue: Issue) -> IssueModel | None:
        return self._session.scalar(
            select(IssueModel).where(
                IssueModel.year == issue.year,
                IssueModel.number == issue.number,
            )
        )

    def _find_id(self, issue: Issue) -> int | None:
        return self._session.scalar(
            select(IssueModel.id).where(
                IssueModel.year == issue.year,
                IssueModel.number == issue.number,
            )
        )
