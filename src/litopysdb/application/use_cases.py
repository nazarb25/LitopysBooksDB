from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from litopysdb.application.ports import (
    BookExtractor,
    IssueCatalog,
    IssueDownloader,
    PdfArchive,
    SearchQuery,
    UnitOfWorkFactory,
)
from litopysdb.domain.models import Book, Issue


@dataclass(frozen=True, slots=True)
class ImportResult:
    issue: Issue
    books: int
    skipped: bool


@dataclass(frozen=True, slots=True)
class SyncOutcome:
    issue: Issue
    result: ImportResult | None
    error: str | None


class ImportIssue:
    def __init__(self, extractor: BookExtractor, uow_factory: UnitOfWorkFactory) -> None:
        self.extractor = extractor
        self.uow_factory = uow_factory

    def execute(self, issue: Issue, pdf: bytes) -> ImportResult:
        digest = sha256(pdf + b"litopysdb-parser-v6").hexdigest()
        with self.uow_factory() as uow:
            if uow.books.is_current(issue, digest):
                return ImportResult(issue, 0, True)
        parsed = self.extractor.extract(issue, pdf)
        if not parsed.books:
            raise ValueError(f"No bibliographic records found in {issue.url}")
        with self.uow_factory() as uow:
            uow.books.replace_issue(issue, digest, parsed.month, parsed.books)
            uow.commit()
        return ImportResult(issue, len(parsed.books), False)

    def has_issue(self, issue: Issue) -> bool:
        with self.uow_factory() as uow:
            return uow.books.has_issue(issue)

    def latest_issue(self) -> Issue | None:
        with self.uow_factory() as uow:
            return uow.books.latest_issue()


class SyncCatalog:
    def __init__(
        self,
        catalog: IssueCatalog,
        downloader: IssueDownloader,
        archive: PdfArchive,
        importer: ImportIssue,
    ) -> None:
        self.catalog = catalog
        self.downloader = downloader
        self.archive = archive
        self.importer = importer

    def execute(
        self,
        *,
        since_year: int | None = None,
        limit: int | None = None,
        reuse_downloaded: bool = False,
        mode: Literal["new", "missing", "refresh"] = "new",
    ) -> Iterator[SyncOutcome]:
        if mode not in {"new", "missing", "refresh"}:
            raise ValueError(f"Unknown sync mode: {mode}")
        issues = [
            issue
            for issue in self.catalog.list_issues()
            if since_year is None or issue.year >= since_year
        ]
        if mode == "new":
            latest = self.importer.latest_issue()
            if latest is not None:
                issues = [
                    issue
                    for issue in issues
                    if (issue.year, issue.number) > (latest.year, latest.number)
                ]
        elif mode == "missing":
            issues = [issue for issue in issues if not self.importer.has_issue(issue)]
        if limit is not None:
            issues = issues[:limit]
        for issue in issues:
            try:
                pdf = self.archive.load(issue) if reuse_downloaded else None
                if pdf is None:
                    pdf = self.downloader.download(issue)
                    self.archive.save(issue, pdf)
                yield SyncOutcome(issue, self.importer.execute(issue, pdf), None)
            except Exception as exc:  # noqa: BLE001 - isolate failures per remote issue
                yield SyncOutcome(issue, None, str(exc))


class SearchBooks:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self, query: SearchQuery) -> Sequence[Book]:
        with self.uow_factory() as uow:
            return uow.books.search(query)

    def count(self, query: SearchQuery) -> int:
        with self.uow_factory() as uow:
            return uow.books.count_search(query)


class BackfillIssueMonths:
    def __init__(
        self,
        extractor: BookExtractor,
        archive: PdfArchive,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self.extractor = extractor
        self.archive = archive
        self.uow_factory = uow_factory

    def execute(self) -> tuple[int, int]:
        with self.uow_factory() as uow:
            issues = uow.books.issues_missing_month()
        updated = missing = 0
        for issue in issues:
            pdf = self.archive.load(issue)
            if pdf is None:
                missing += 1
                continue
            month = self.extractor.extract_month(issue, pdf)
            if month is None:
                missing += 1
                continue
            with self.uow_factory() as uow:
                uow.books.set_issue_month(issue, month)
                uow.commit()
            updated += 1
        return updated, missing


class BackfillBookDetails:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self.uow_factory = uow_factory

    def execute(self) -> int:
        with self.uow_factory() as uow:
            updated = uow.books.backfill_details()
            uow.commit()
        return updated
