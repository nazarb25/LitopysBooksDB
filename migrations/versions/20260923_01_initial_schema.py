"""Create the initial catalog schema.

Revision ID: 20260923_01
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260923_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "issues" not in tables:
        op.create_table(
            "issues",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("url", sa.Text(), nullable=False, unique=True),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("number", sa.Integer(), nullable=False),
            sa.Column("month", sa.Integer(), nullable=True),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.UniqueConstraint("year", "number"),
        )
    elif "month" not in {column["name"] for column in inspector.get_columns("issues")}:
        op.add_column("issues", sa.Column("month", sa.Integer(), nullable=True))

    inspector = sa.inspect(op.get_bind())
    if "books" not in set(inspector.get_table_names()):
        op.create_table(
            "books",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("issue_id", sa.Integer(), nullable=False),
            sa.Column("record_number", sa.Integer(), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("title_key", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("source_page", sa.Integer(), nullable=False),
            sa.Column("author", sa.Text(), nullable=True),
            sa.Column("author_key", sa.Text(), nullable=True),
            sa.Column("isbn", sa.String(length=32), nullable=True),
            sa.Column("publication_year", sa.Integer(), nullable=True),
            sa.Column("responsibility", sa.Text(), nullable=True),
            sa.Column("publication_place", sa.Text(), nullable=True),
            sa.Column("publisher", sa.Text(), nullable=True),
            sa.Column("physical_description", sa.Text(), nullable=True),
            sa.Column("print_run", sa.Integer(), nullable=True),
            sa.Column("catalog_number", sa.String(length=32), nullable=True),
            sa.Column("udc", sa.Text(), nullable=True),
            sa.Column("original_title", sa.Text(), nullable=True),
            sa.Column("original_isbn", sa.String(length=32), nullable=True),
            sa.Column("translators", sa.Text(), nullable=True),
            sa.Column("editors", sa.Text(), nullable=True),
            sa.Column("illustrators", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("issue_id", "record_number"),
        )
        op.create_index("ix_books_author_key", "books", ["author_key"])
        op.create_index("ix_books_title_key", "books", ["title_key"])
        op.create_index("ix_books_publication_year", "books", ["publication_year"])
    else:
        existing = {column["name"] for column in inspector.get_columns("books")}
        additions = {
            "responsibility": sa.Text(),
            "publication_place": sa.Text(),
            "publisher": sa.Text(),
            "physical_description": sa.Text(),
            "print_run": sa.Integer(),
            "catalog_number": sa.String(length=32),
            "udc": sa.Text(),
            "original_title": sa.Text(),
            "original_isbn": sa.String(length=32),
            "translators": sa.Text(),
            "editors": sa.Text(),
            "illustrators": sa.Text(),
        }
        for name, type_ in additions.items():
            if name not in existing:
                op.add_column("books", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    op.drop_table("books")
    op.drop_table("issues")
