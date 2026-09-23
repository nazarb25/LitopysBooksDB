from sqlalchemy import Select, false, func, select, text
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
        full_text_query = SqlAlchemyBookCatalogReadRepository._build_full_text_query(query)
        if full_text_query == "":
            statement = statement.where(false())
        elif full_text_query is not None:
            statement = statement.where(
                text(
                    "books.id IN ("
                    "SELECT rowid FROM books_fts WHERE books_fts MATCH :full_text_query"
                    ")"
                )
            ).params(full_text_query=full_text_query)
        if query.year is not None:
            statement = statement.where(BookModel.publication_year == query.year)
        if query.issue_year is not None:
            statement = statement.where(IssueModel.year == query.issue_year)
        if query.issue_month is not None:
            statement = statement.where(IssueModel.month == query.issue_month)
        if query.issue_number is not None:
            statement = statement.where(IssueModel.number == query.issue_number)
        if query.print_run_min is not None:
            statement = statement.where(BookModel.print_run >= query.print_run_min)
        if query.print_run_max is not None:
            statement = statement.where(BookModel.print_run <= query.print_run_max)
        return statement

    @staticmethod
    def _build_full_text_query(query: SearchBooksQuery) -> str | None:
        filters = (
            ("author_key", query.author),
            ("{title_key description}", query.text),
            ("publisher", query.publisher),
            ("publication_place", query.publication_place),
            ("translators", query.translator),
            ("editors", query.editor),
            ("illustrators", query.illustrator),
            ("original_title", query.original_title),
            ("isbn", query.isbn),
            ("original_isbn", query.original_isbn),
            ("udc", query.udc),
            ("catalog_number", query.catalog_number),
            ("responsibility", query.responsibility),
            ("physical_description", query.physical_description),
        )
        clauses = []
        for columns, value in filters:
            if not value:
                continue
            tokens = BookMapper.search_key(value).split()
            if not tokens:
                return ""
            terms = " AND ".join(f'"{token}"' for token in tokens)
            clauses.append(f"({columns} : ({terms}))")
        return " AND ".join(clauses) or None
