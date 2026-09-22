from app.application.dto.issue_import import ParsedBookDetailsDTO
from app.application.interfaces.services.bibliographic_parser import BibliographicParser
from app.application.interfaces.unit_of_work import UnitOfWorkFactory


class BackfillBookDetailsUseCase:
    def __init__(
        self,
        parser: BibliographicParser,
        uow_factory: UnitOfWorkFactory,
        *,
        batch_size: int = 5_000,
    ) -> None:
        self._parser = parser
        self._uow_factory = uow_factory
        self._batch_size = batch_size

    def execute(self) -> int:
        updated = 0
        after_id = 0
        while True:
            with self._uow_factory() as uow:
                sources = tuple(
                    uow.issues.list_book_details_sources(
                        after_id=after_id,
                        limit=self._batch_size,
                    )
                )
            if not sources:
                return updated

            records: list[ParsedBookDetailsDTO] = []
            for source in sources:
                details = self._parser.parse(source.description)
                records.append(
                    ParsedBookDetailsDTO(
                        id=source.id,
                        isbn=self._parser.primary_isbn(source.description),
                        responsibility=details.responsibility,
                        publication_place=details.publication_place,
                        publisher=details.publisher,
                        physical_description=details.physical_description,
                        print_run=details.print_run,
                        catalog_number=details.catalog_number,
                        udc=details.udc,
                        original_title=details.original_title,
                        original_isbn=details.original_isbn,
                        translators=details.translators,
                        editors=details.editors,
                        illustrators=details.illustrators,
                    )
                )
            with self._uow_factory() as uow:
                uow.issues.update_book_details(records)
                uow.commit()
            after_id = sources[-1].id
            updated += len(sources)
