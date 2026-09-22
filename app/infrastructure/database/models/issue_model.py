from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.book_model import BookModel


class IssueModel(Base):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("year", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    year: Mapped[int] = mapped_column(Integer)
    number: Mapped[int] = mapped_column(Integer)
    month: Mapped[int | None] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    books: Mapped[list[BookModel]] = relationship(
        back_populates="issue",
        cascade="all, delete-orphan",
    )
