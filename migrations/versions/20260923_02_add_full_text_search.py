"""Add the full-text catalog search index.

Revision ID: 20260923_02
Revises: 20260923_01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260923_02"
down_revision: str | None = "20260923_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    "author_key",
    "title_key",
    "description",
    "responsibility",
    "publication_place",
    "publisher",
    "physical_description",
    "catalog_number",
    "udc",
    "original_title",
    "original_isbn",
    "translators",
    "editors",
    "illustrators",
    "isbn",
)
_COLUMN_LIST = ", ".join(_COLUMNS)
_NEW_COLUMN_LIST = ", ".join(f"new.{column}" for column in _COLUMNS)
_OLD_COLUMN_LIST = ", ".join(f"old.{column}" for column in _COLUMNS)


def upgrade() -> None:
    op.drop_index("ix_books_title_key", table_name="books")
    op.drop_index("ix_books_author_key", table_name="books")
    op.execute(
        f"""
        CREATE VIRTUAL TABLE books_fts USING fts5(
            {_COLUMN_LIST},
            content='books',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER books_fts_after_insert AFTER INSERT ON books BEGIN
            INSERT INTO books_fts(rowid, {_COLUMN_LIST})
            VALUES (new.id, {_NEW_COLUMN_LIST});
        END
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER books_fts_after_delete AFTER DELETE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, {_COLUMN_LIST})
            VALUES ('delete', old.id, {_OLD_COLUMN_LIST});
        END
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER books_fts_after_update AFTER UPDATE ON books BEGIN
            INSERT INTO books_fts(books_fts, rowid, {_COLUMN_LIST})
            VALUES ('delete', old.id, {_OLD_COLUMN_LIST});
            INSERT INTO books_fts(rowid, {_COLUMN_LIST})
            VALUES (new.id, {_NEW_COLUMN_LIST});
        END
        """
    )
    op.execute("INSERT INTO books_fts(books_fts) VALUES ('rebuild')")
    op.create_index("ix_books_print_run", "books", ["print_run"])


def downgrade() -> None:
    op.drop_index("ix_books_print_run", table_name="books")
    op.execute("DROP TRIGGER books_fts_after_update")
    op.execute("DROP TRIGGER books_fts_after_delete")
    op.execute("DROP TRIGGER books_fts_after_insert")
    op.execute("DROP TABLE books_fts")
    op.create_index("ix_books_author_key", "books", ["author_key"])
    op.create_index("ix_books_title_key", "books", ["title_key"])
