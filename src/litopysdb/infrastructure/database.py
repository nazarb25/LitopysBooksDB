import re
from collections.abc import Sequence
from pathlib import Path
from typing import Self

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from litopysdb.application.ports import SearchQuery
from litopysdb.domain.models import BibliographicDetails, Book, Issue
from litopysdb.infrastructure.bibliography import parse_bibliographic_details, primary_isbn


class Base(DeclarativeBase):
    pass


class IssueRow(Base):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("year", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    year: Mapped[int] = mapped_column(Integer)
    number: Mapped[int] = mapped_column(Integer)
    month: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    books: Mapped[list[BookRow]] = relationship(
        back_populates="issue", cascade="all, delete-orphan"
    )


class BookRow(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("issue_id", "record_number"),
        Index("ix_books_author_key", "author_key"),
        Index("ix_books_title_key", "title_key"),
        Index("ix_books_publication_year", "publication_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"))
    record_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)
    title_key: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    source_page: Mapped[int] = mapped_column(Integer)
    author: Mapped[str | None] = mapped_column(Text)
    author_key: Mapped[str | None] = mapped_column(Text)
    isbn: Mapped[str | None] = mapped_column(String(32))
    publication_year: Mapped[int | None] = mapped_column(Integer)
    responsibility: Mapped[str | None] = mapped_column(Text)
    publication_place: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(Text)
    physical_description: Mapped[str | None] = mapped_column(Text)
    print_run: Mapped[int | None] = mapped_column(Integer)
    catalog_number: Mapped[str | None] = mapped_column(String(32))
    udc: Mapped[str | None] = mapped_column(Text)
    original_title: Mapped[str | None] = mapped_column(Text)
    original_isbn: Mapped[str | None] = mapped_column(String(32))
    translators: Mapped[str | None] = mapped_column(Text)
    editors: Mapped[str | None] = mapped_column(Text)
    illustrators: Mapped[str | None] = mapped_column(Text)
    issue: Mapped[IssueRow] = relationship(back_populates="books")


def _key(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold()))


def _author_key(value: str | None) -> str | None:
    if not value:
        return None
    tokens = _key(value).split()
    if len(tokens) >= 2:
        return " ".join(tokens + [tokens[-1], tokens[0][0]])
    return " ".join(tokens)


def _to_domain(row: BookRow) -> Book:
    return Book(
        issue_url=row.issue.url,
        record_number=row.record_number,
        title=row.title,
        description=row.description,
        source_page=row.source_page,
        author=row.author,
        isbn=row.isbn,
        publication_year=row.publication_year,
        issue_year=row.issue.year,
        issue_number=row.issue.number,
        issue_month=row.issue.month,
        details=BibliographicDetails(
            responsibility=row.responsibility,
            publication_place=row.publication_place,
            publisher=row.publisher,
            physical_description=row.physical_description,
            print_run=row.print_run,
            catalog_number=row.catalog_number,
            udc=row.udc,
            original_title=row.original_title,
            original_isbn=row.original_isbn,
            translators=row.translators,
            editors=row.editors,
            illustrators=row.illustrators,
        ),
    )


class SqlBookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_current(self, issue: Issue, digest: str) -> bool:
        row = self.session.scalar(
            select(IssueRow).where(IssueRow.year == issue.year, IssueRow.number == issue.number)
        )
        return row is not None and row.sha256 == digest

    def has_issue(self, issue: Issue) -> bool:
        return (
            self.session.scalar(
                select(IssueRow.id).where(
                    IssueRow.year == issue.year, IssueRow.number == issue.number
                )
            )
            is not None
        )

    def latest_issue(self) -> Issue | None:
        row = self.session.scalar(
            select(IssueRow).order_by(IssueRow.year.desc(), IssueRow.number.desc()).limit(1)
        )
        return Issue(row.url, row.year, row.number) if row is not None else None

    def replace_issue(
        self, issue: Issue, digest: str, month: int | None, books: Sequence[Book]
    ) -> None:
        row = self.session.scalar(
            select(IssueRow).where(IssueRow.year == issue.year, IssueRow.number == issue.number)
        )
        if row is None:
            row = IssueRow(
                url=issue.url, year=issue.year, number=issue.number, month=month, sha256=digest
            )
            self.session.add(row)
        else:
            row.url = issue.url
            row.sha256 = digest
            row.month = month
            row.books.clear()
            self.session.flush()
        row.books.extend(
            BookRow(
                record_number=book.record_number,
                title=book.title,
                title_key=_key(book.title),
                description=book.description,
                source_page=book.source_page,
                author=book.author,
                author_key=_author_key(book.author),
                isbn=book.isbn,
                publication_year=book.publication_year,
                responsibility=book.details.responsibility,
                publication_place=book.details.publication_place,
                publisher=book.details.publisher,
                physical_description=book.details.physical_description,
                print_run=book.details.print_run,
                catalog_number=book.details.catalog_number,
                udc=book.details.udc,
                original_title=book.details.original_title,
                original_isbn=book.details.original_isbn,
                translators=book.details.translators,
                editors=book.details.editors,
                illustrators=book.details.illustrators,
            )
            for book in books
        )

    def _apply_search_filters(self, statement, query: SearchQuery):
        if query.author:
            statement = statement.where(BookRow.author_key.contains(_key(query.author)))
        if query.text:
            pattern = _key(query.text)
            # Full bibliographic descriptions retain information not extracted into fields.
            statement = statement.where(
                BookRow.title_key.contains(pattern) | BookRow.description.ilike(f"%{query.text}%")
            )
        if query.year is not None:
            statement = statement.where(BookRow.publication_year == query.year)
        if query.issue_year is not None:
            statement = statement.where(IssueRow.year == query.issue_year)
        if query.issue_month is not None:
            statement = statement.where(IssueRow.month == query.issue_month)
        if query.issue_number is not None:
            statement = statement.where(IssueRow.number == query.issue_number)
        text_filters = (
            (BookRow.publisher, query.publisher),
            (BookRow.publication_place, query.publication_place),
            (BookRow.translators, query.translator),
            (BookRow.editors, query.editor),
            (BookRow.illustrators, query.illustrator),
            (BookRow.original_title, query.original_title),
            (BookRow.isbn, query.isbn),
            (BookRow.original_isbn, query.original_isbn),
            (BookRow.udc, query.udc),
            (BookRow.catalog_number, query.catalog_number),
            (BookRow.responsibility, query.responsibility),
            (BookRow.physical_description, query.physical_description),
        )
        for column, value in text_filters:
            if value:
                statement = statement.where(column.ilike(f"%{value}%"))
        if query.print_run_min is not None:
            statement = statement.where(BookRow.print_run >= query.print_run_min)
        if query.print_run_max is not None:
            statement = statement.where(BookRow.print_run <= query.print_run_max)
        return statement

    def search(self, query: SearchQuery) -> list[Book]:
        statement = self._apply_search_filters(select(BookRow).join(BookRow.issue), query)
        statement = statement.order_by(
            IssueRow.year.desc(), IssueRow.number.desc(), BookRow.record_number
        )
        statement = statement.limit(query.limit).offset(query.offset)
        return [_to_domain(row) for row in self.session.scalars(statement).all()]

    def count_search(self, query: SearchQuery) -> int:
        statement = self._apply_search_filters(
            select(func.count()).select_from(BookRow).join(BookRow.issue), query
        )
        return self.session.scalar(statement) or 0

    def issues_missing_month(self) -> list[Issue]:
        rows = self.session.scalars(select(IssueRow).where(IssueRow.month.is_(None))).all()
        return [Issue(row.url, row.year, row.number) for row in rows]

    def set_issue_month(self, issue: Issue, month: int) -> None:
        row = self.session.scalar(
            select(IssueRow).where(IssueRow.year == issue.year, IssueRow.number == issue.number)
        )
        if row is None:
            raise ValueError(f"Issue {issue.year} #{issue.number} is not indexed")
        row.month = month

    def backfill_details(self, batch_size: int = 5000) -> int:
        updated = 0
        last_id = 0
        while True:
            rows = self.session.scalars(
                select(BookRow).where(BookRow.id > last_id).order_by(BookRow.id).limit(batch_size)
            ).all()
            if not rows:
                break
            for row in rows:
                details = parse_bibliographic_details(row.description)
                row.isbn = primary_isbn(row.description) or row.isbn
                row.responsibility = details.responsibility
                row.publication_place = details.publication_place
                row.publisher = details.publisher
                row.physical_description = details.physical_description
                row.print_run = details.print_run
                row.catalog_number = details.catalog_number
                row.udc = details.udc
                row.original_title = details.original_title
                row.original_isbn = details.original_isbn
                row.translators = details.translators
                row.editors = details.editors
                row.illustrators = details.illustrators
            last_id = rows[-1].id
            updated += len(rows)
            self.session.commit()
            self.session.expunge_all()
        return updated

    def count_issues(self) -> int:
        from sqlalchemy import func

        return self.session.scalar(select(func.count()).select_from(IssueRow)) or 0

    def count_books(self) -> int:
        from sqlalchemy import func

        return self.session.scalar(select(func.count()).select_from(BookRow)) or 0


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def __enter__(self) -> Self:
        self.session = self.session_factory()
        self.books = SqlBookRepository(self.session)
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()


def make_uow_factory(database_path: Path) -> tuple[sessionmaker[Session], type[SqlUnitOfWork]]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    if "month" not in {column["name"] for column in inspect(engine).get_columns("issues")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE issues ADD COLUMN month INTEGER"))
    book_columns = {column["name"] for column in inspect(engine).get_columns("books")}
    detail_columns = {
        "responsibility": "TEXT",
        "publication_place": "TEXT",
        "publisher": "TEXT",
        "physical_description": "TEXT",
        "print_run": "INTEGER",
        "catalog_number": "VARCHAR(32)",
        "udc": "TEXT",
        "original_title": "TEXT",
        "original_isbn": "VARCHAR(32)",
        "translators": "TEXT",
        "editors": "TEXT",
        "illustrators": "TEXT",
    }
    missing_columns = detail_columns.keys() - book_columns
    if missing_columns:
        with engine.begin() as connection:
            for column in missing_columns:
                connection.execute(
                    text(f"ALTER TABLE books ADD COLUMN {column} {detail_columns[column]}")
                )
    return sessionmaker(engine, expire_on_commit=False), SqlUnitOfWork
