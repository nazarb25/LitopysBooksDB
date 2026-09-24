from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.infrastructure.database.database import create_database_engine


def test_read_only_database_can_be_queried_but_not_changed(tmp_path: Path) -> None:
    database_path = tmp_path / "catalog.db"
    writable_engine = create_database_engine(database_path)
    with writable_engine.begin() as connection:
        connection.execute(text("CREATE TABLE sample (value TEXT NOT NULL)"))
        connection.execute(text("INSERT INTO sample VALUES ('ok')"))
    writable_engine.dispose()

    read_only_engine = create_database_engine(database_path, read_only=True)
    with read_only_engine.connect() as connection:
        assert connection.scalar(text("SELECT value FROM sample")) == "ok"
        with pytest.raises(OperationalError):
            connection.execute(text("INSERT INTO sample VALUES ('changed')"))
    read_only_engine.dispose()
