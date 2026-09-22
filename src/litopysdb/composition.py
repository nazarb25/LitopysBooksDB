from pathlib import Path

from litopysdb.application.use_cases import ImportIssue, SearchBooks
from litopysdb.infrastructure.database import SqlUnitOfWork, make_uow_factory
from litopysdb.infrastructure.pdf import PyMuPdfExtractor

DEFAULT_DB = Path("data/litopys.db")


def build_use_cases(database_path: Path) -> tuple[ImportIssue, SearchBooks, object]:
    sessions, _ = make_uow_factory(database_path)
    uow_factory = lambda: SqlUnitOfWork(sessions)
    return ImportIssue(PyMuPdfExtractor(), uow_factory), SearchBooks(uow_factory), uow_factory
