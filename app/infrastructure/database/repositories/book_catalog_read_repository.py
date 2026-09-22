from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.dto.book_search import BookSearchPageDTO, SearchBooksQuery
from app.application.dto.statistics import CatalogStatisticsDTO
from app.infrastructure.database.mappers.book_mapper import BookMapper
from app.infrastructure.database.models import BookModel, IssueModel


class SqlAlchemyBookCatalogReadRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def search(self, query: SearchBooksQuery) -> BookSearchPageDTO:
        with self._session_factory() as session:
            count_statement = self._apply_filters(
                select(func.count()).select_from(BookModel).join(BookModel.issue),
                query,
            )
            total = session.scalar(count_statement) or 0
            statement = self._apply_filters(
                select(BookModel, IssueModel).join(BookModel.issue),
                query,
            )
            statement = (
                statement.order_by(
                    IssueModel.year.desc(),
                    IssueModel.number.desc(),
                    BookModel.record_number,
                )
                .limit(query.limit)
                .offset(query.offset)
            )
            items = tuple(
                BookMapper.to_dto(book, issue) for book, issue in session.execute(statement).all()
            )
        return BookSearchPageDTO(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    def get_statistics(self) -> CatalogStatisticsDTO:
        with self._session_factory() as session:
            issues = session.scalar(select(func.count()).select_from(IssueModel)) or 0
            books = session.scalar(select(func.count()).select_from(BookModel)) or 0
        return CatalogStatisticsDTO(issues=issues, books=books)

    @staticmethod
    def _apply_filters(statement: Select[tuple], query: SearchBooksQuery) -> Select[tuple]:
        if query.author:
            statement = statement.where(
                BookModel.author_key.contains(BookMapper.search_key(query.author))
            )
        if query.text:
            key = BookMapper.search_key(query.text)
            statement = statement.where(
                BookModel.title_key.contains(key) | BookModel.description.ilike(f"%{query.text}%")
            )
        if query.year is not None:
            statement = statement.where(BookModel.publication_year == query.year)
        if query.issue_year is not None:
            statement = statement.where(IssueModel.year == query.issue_year)
        if query.issue_month is not None:
            statement = statement.where(IssueModel.month == query.issue_month)
        if query.issue_number is not None:
            statement = statement.where(IssueModel.number == query.issue_number)
        text_filters = (
            (BookModel.publisher, query.publisher),
            (BookModel.publication_place, query.publication_place),
            (BookModel.translators, query.translator),
            (BookModel.editors, query.editor),
            (BookModel.illustrators, query.illustrator),
            (BookModel.original_title, query.original_title),
            (BookModel.isbn, query.isbn),
            (BookModel.original_isbn, query.original_isbn),
            (BookModel.udc, query.udc),
            (BookModel.catalog_number, query.catalog_number),
            (BookModel.responsibility, query.responsibility),
            (BookModel.physical_description, query.physical_description),
        )
        for column, value in text_filters:
            if value:
                statement = statement.where(column.ilike(f"%{value}%"))
        if query.print_run_min is not None:
            statement = statement.where(BookModel.print_run >= query.print_run_min)
        if query.print_run_max is not None:
            statement = statement.where(BookModel.print_run <= query.print_run_max)
        return statement
