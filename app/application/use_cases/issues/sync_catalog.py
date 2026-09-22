from collections.abc import Iterator
from typing import Literal

from app.application.dto.issue_import import SyncIssueOutcomeDTO
from app.application.interfaces.services.issue_catalog import IssueCatalog
from app.application.interfaces.services.issue_downloader import IssueDownloader
from app.application.interfaces.services.pdf_archive import PdfArchive
from app.application.use_cases.issues.import_issue import ImportIssueUseCase


class SyncCatalogUseCase:
    def __init__(
        self,
        catalog: IssueCatalog,
        downloader: IssueDownloader,
        archive: PdfArchive,
        importer: ImportIssueUseCase,
    ) -> None:
        self._catalog = catalog
        self._downloader = downloader
        self._archive = archive
        self._importer = importer

    def execute(
        self,
        *,
        since_year: int | None = None,
        limit: int | None = None,
        reuse_downloaded: bool = False,
        mode: Literal["new", "missing", "refresh"] = "new",
    ) -> Iterator[SyncIssueOutcomeDTO]:
        if mode not in {"new", "missing", "refresh"}:
            raise ValueError(f"Unknown sync mode: {mode}")

        issues = [
            issue
            for issue in self._catalog.list_issues()
            if since_year is None or issue.year >= since_year
        ]
        if mode == "new":
            latest = self._importer.latest_issue()
            if latest is not None:
                issues = [
                    issue
                    for issue in issues
                    if (issue.year, issue.number) > (latest.year, latest.number)
                ]
        elif mode == "missing":
            issues = [issue for issue in issues if not self._importer.has_issue(issue)]
        if limit is not None:
            issues = issues[:limit]

        for issue in issues:
            try:
                pdf = self._archive.load(issue) if reuse_downloaded else None
                if pdf is None:
                    pdf = self._downloader.download(issue)
                    self._archive.save(issue, pdf)
                result = self._importer.execute(issue, pdf)
                yield SyncIssueOutcomeDTO(issue=issue, result=result, error=None)
            except Exception as exc:  # noqa: BLE001 - one remote issue must not stop the sync
                yield SyncIssueOutcomeDTO(issue=issue, result=None, error=str(exc))
