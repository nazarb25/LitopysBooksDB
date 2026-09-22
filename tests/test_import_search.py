import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text

from litopysdb.application.ports import SearchQuery
from litopysdb.application.use_cases import (
    BackfillIssueMonths,
    ImportIssue,
    SearchBooks,
    SyncCatalog,
)
from litopysdb.domain.models import BibliographicDetails, Book, Issue, ParsedIssue
from litopysdb.infrastructure.database import SqlUnitOfWork, make_uow_factory
from litopysdb.infrastructure.pdf import _book, _month_from_cover

ISSUE = Issue("https://ukrbook.net/litopys/Knigki/2026/L_k_16_2026.pdf", 2026, 16)


class FakeExtractor:
    def extract(self, issue: Issue, pdf: bytes) -> ParsedIssue:
        return ParsedIssue(
            (
                Book(
                    issue.url,
                    7701,
                    "Темна вежа",
                    "Кінг С. Темна вежа / Стівен Кінг. — Київ, 2025.",
                    5,
                    "Кінг С.",
                    "978-617-123-456-7",
                    2025,
                    details=BibliographicDetails(
                        responsibility="Стівен Кінг ; пер. з англ. І. Перекладача",
                        publication_place="Харків",
                        publisher="КСД",
                        physical_description="500 с. ; 21 см",
                        print_run=3000,
                        catalog_number="2026-07701",
                        udc="821.111",
                        original_title="The Dark Tower",
                        original_isbn="978-1-234-56789-0",
                        translators="І. Перекладача",
                        editors="Р. Редактора",
                        illustrators="Х. Художника",
                    ),
                ),
            ),
            8,
        )

    def extract_month(self, issue: Issue, pdf: bytes) -> int | None:
        return 8


def _cases(path: Path):
    sessions, _ = make_uow_factory(path)
    factory = lambda: SqlUnitOfWork(sessions)
    return ImportIssue(FakeExtractor(), factory), SearchBooks(factory), factory


def test_import_is_idempotent_and_author_search_uses_creator(tmp_path):
    importer, finder, factory = _cases(tmp_path / "books.db")
    first = importer.execute(ISSUE, b"pdf")
    second = importer.execute(ISSUE, b"pdf")
    assert first.books == 1 and not first.skipped
    assert second.skipped
    assert importer.has_issue(ISSUE)
    assert len(finder.execute(SearchQuery(author="Кінг С."))) == 1
    assert finder.count(SearchQuery(author="Кінг С.")) == 1
    assert finder.count(SearchQuery(author="Стівен Кінг")) == 0
    assert finder.count(SearchQuery(publisher="КСД")) == 1
    assert finder.count(SearchQuery(publication_place="Харків")) == 1
    assert finder.count(SearchQuery(translator="Перекладача")) == 1
    assert finder.count(SearchQuery(editor="Редактора")) == 1
    assert finder.count(SearchQuery(illustrator="Художника")) == 1
    assert finder.count(SearchQuery(original_title="Dark Tower")) == 1
    assert finder.count(SearchQuery(original_isbn="1-234")) == 1
    assert finder.count(SearchQuery(udc="821.111")) == 1
    assert finder.count(SearchQuery(catalog_number="07701")) == 1
    assert finder.count(SearchQuery(print_run_min=3000, print_run_max=3000)) == 1
    assert len(finder.execute(SearchQuery(author="Стівен Кінг"))) == 0
    assert len(finder.execute(SearchQuery(issue_year=2026, issue_month=8))) == 1
    assert len(finder.execute(SearchQuery(issue_number=16))) == 1
    assert len(finder.execute(SearchQuery(issue_number=15))) == 0
    assert len(finder.execute(SearchQuery(issue_year=2026, issue_month=7))) == 0
    with factory() as uow:
        assert uow.books.count_books() == 1


def test_failed_parse_keeps_existing_data(tmp_path):
    importer, finder, _ = _cases(tmp_path / "books.db")
    importer.execute(ISSUE, b"pdf")

    class BrokenExtractor:
        def extract(self, issue, pdf):
            raise ValueError("incomplete issue")

    broken = ImportIssue(BrokenExtractor(), importer.uow_factory)
    with pytest.raises(ValueError, match="incomplete"):
        broken.execute(ISSUE, b"changed pdf")
    assert len(finder.execute(SearchQuery(text="Темна вежа"))) == 1


def test_sync_does_nothing_when_catalog_has_no_new_issue(tmp_path):
    importer, _, _ = _cases(tmp_path / "books.db")
    importer.execute(ISSUE, b"pdf")

    class Catalog:
        def list_issues(self):
            return [ISSUE]

    class Downloader:
        def download(self, issue):
            raise AssertionError("Already indexed issue should not be downloaded")

    class Archive:
        def load(self, issue):
            raise AssertionError("Already indexed issue should not be read")

        def save(self, issue, pdf):
            raise AssertionError("Already indexed issue should not be saved")

    assert list(SyncCatalog(Catalog(), Downloader(), Archive(), importer).execute()) == []


def test_sync_downloads_only_issues_after_latest_indexed(tmp_path):
    importer, _, _ = _cases(tmp_path / "books.db")
    importer.execute(ISSUE, b"pdf")
    old_gap = Issue(ISSUE.url.replace("16_2026", "15_2026"), 2026, 15)
    new_issue = Issue(ISSUE.url.replace("16_2026", "17_2026"), 2026, 17)

    class Catalog:
        def list_issues(self):
            return [old_gap, ISSUE, new_issue]

    class Downloader:
        def __init__(self):
            self.calls = []

        def download(self, issue):
            self.calls.append(issue.number)
            return b"pdf"

    class Archive:
        def load(self, issue):
            return None

        def save(self, issue, pdf):
            pass

    downloader = Downloader()
    sync = SyncCatalog(Catalog(), downloader, Archive(), importer)
    outcomes = list(sync.execute(limit=1))
    assert [outcome.issue.number for outcome in outcomes] == [17]
    assert downloader.calls == [17]
    assert list(sync.execute()) == []
    assert [outcome.issue.number for outcome in sync.execute(mode="missing")] == [15]
    assert downloader.calls == [17, 15]


def test_record_parsing_preserves_full_title_and_identifies_author():
    book = _book(
        ISSUE,
        7702,
        5,
        "Вікович І. А. Методи наукових досліджень : навч. посіб. / І. А. Вікович. "
        "— Львів : Видавництво, 2025. — ISBN 978-966-994-073-5.",
    )
    assert book.author == "Вікович І. А"
    assert book.title == "Методи наукових досліджень : навч. посіб"
    assert book.publication_year == 2025
    assert book.isbn == "978-966-994-073-5"


def test_backfill_issue_month_from_archived_pdf(tmp_path):
    importer, finder, factory = _cases(tmp_path / "books.db")
    importer.execute(ISSUE, b"pdf")
    with factory() as uow:
        uow.books.session.execute(text("UPDATE issues SET month = NULL"))
        uow.commit()

    class Archive:
        def load(self, issue):
            return b"pdf"

    assert BackfillIssueMonths(FakeExtractor(), Archive(), factory).execute() == (1, 0)
    assert len(finder.execute(SearchQuery(issue_month=8))) == 1


def test_cover_month_and_existing_database_migration(tmp_path):
    assert _month_from_cover("№ 11\nЧервень, 2025", 2025) == 6
    assert _month_from_cover("№ 15\nCерпень 2008", 2008) == 8
    assert _month_from_cover("№ 11\nЧервень, 2025", 2024) is None

    path = tmp_path / "old.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE issues (id INTEGER PRIMARY KEY, url TEXT, year INTEGER, "
            "number INTEGER, sha256 TEXT)"
        )
    make_uow_factory(path)
    with sqlite3.connect(path) as connection:
        columns = [column[1] for column in connection.execute("PRAGMA table_info(issues)")]
    assert "month" in columns


def test_invalid_print_run_range_is_rejected():
    with pytest.raises(ValueError, match="must not exceed"):
        SearchQuery(print_run_min=5000, print_run_max=1000)
