from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BibliographicDetails:
    responsibility: str | None = None
    publication_place: str | None = None
    publisher: str | None = None
    physical_description: str | None = None
    print_run: int | None = None
    catalog_number: str | None = None
    udc: str | None = None
    original_title: str | None = None
    original_isbn: str | None = None
    translators: str | None = None
    editors: str | None = None
    illustrators: str | None = None
