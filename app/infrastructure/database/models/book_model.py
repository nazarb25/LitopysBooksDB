from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models.issue_model import IssueModel


class BookModel(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("issue_id", "record_number"),
        Index("ix_books_publication_year", "publication_year"),
        Index("ix_books_print_run", "print_run"),
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
    issue: Mapped[IssueModel] = relationship(back_populates="books")
