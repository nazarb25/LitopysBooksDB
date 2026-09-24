from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(database_path: Path, *, read_only: bool = False) -> Engine:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if read_only:
        database_uri = f"file:{database_path.resolve()}?mode=ro&immutable=1&uri=true"
        engine = create_engine(f"sqlite:///{database_uri}")
    else:
        engine = create_engine(f"sqlite:///{database_path}")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
