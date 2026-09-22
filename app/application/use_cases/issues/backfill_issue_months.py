from app.application.interfaces.services.book_extractor import BookExtractor
from app.application.interfaces.services.pdf_archive import PdfArchive
from app.application.interfaces.unit_of_work import UnitOfWorkFactory


class BackfillIssueMonthsUseCase:
    def __init__(
        self,
        extractor: BookExtractor,
        archive: PdfArchive,
        uow_factory: UnitOfWorkFactory,
    ) -> None:
        self._extractor = extractor
        self._archive = archive
        self._uow_factory = uow_factory

    def execute(self) -> tuple[int, int]:
        with self._uow_factory() as uow:
            issues = tuple(uow.issues.list_missing_month())
        updated = missing = 0
        for issue in issues:
            pdf = self._archive.load(issue)
            if pdf is None or (month := self._extractor.extract_month(issue, pdf)) is None:
                missing += 1
                continue
            with self._uow_factory() as uow:
                uow.issues.set_month(issue, month)
                uow.commit()
            updated += 1
        return updated, missing
