import re

from litopysdb.domain.models import BibliographicDetails

PUBLICATION = re.compile(
    r"(?:^|\s[—–]\s)([^—–]{1,140}?)\s*:\s*([^—–]{1,180}?),\s*"
    r"(\[?(?:1[89]|20)\d{2}\??\]?)\.\s*[—–]"
)
PHYSICAL_DESCRIPTION = re.compile(r",\s*\[?(?:1[89]|20)\d{2}\??\]?\.\s*[—–]\s*(.+?)(?=\.\s*[—–]\s)")
PRINT_RUN = re.compile(r"(?<!\d)(\d[\d ]{0,8})\s*(?:пр|екз)\.", re.IGNORECASE)
CATALOG_NUMBER = re.compile(r"\[\s*((?:19|20)\d{2}\s*-\s*\d{4,6})\s*\]")
DASH_ISBN = re.compile(
    r"(?:^|\s[—–]\s)[ІI]SBN\s*([0-9XХxх][0-9XХxх\-\s]{8,24}[0-9XХxх])",
    re.IGNORECASE,
)
ORIGINAL_TITLE = re.compile(
    r"(?:Перекладено за вид\.|Назва ориг\.)\s*:\s*(.+?)(?=\s/\s|\.\s*[—–])",
    re.IGNORECASE,
)
RESPONSIBILITY = re.compile(r"\s/\s(.+?)\.\s*[—–]\s")
TRANSLATORS = re.compile(
    r"\bпер\.\s+з\s+\S+\s+(.+?)(?=\s*;\s*|\]|\.\s*[—–]|$)",
    re.IGNORECASE,
)
EDITORS = re.compile(
    r"\b(?:за\s+(?:заг\.\s+)?ред\.|(?:відп\.\s+)?ред(?:кол)?\.?\s*:)\s*"
    r"(.+?)(?=\s*;\s*|\]|\.\s*[—–]|$)",
    re.IGNORECASE,
)
ILLUSTRATORS = re.compile(
    r"\b(?:іл\.|ілюстр\.|худож\.?|худож\.\s*оформ\.?|намалювала)\s*:?[ ]*"
    r"(.+?)(?=\s*;\s*|\]|\.\s*[—–]|$)",
    re.IGNORECASE,
)
CUTTER = re.compile(r"\s+[А-ЯІЇЄҐA-Z][А-ЯІЇЄҐA-Z-]?\d{1,2}\s*$")
INDEX_LEAK = re.compile(r"\s+(?:Див\.|\d{3}(?:\.\d+)*\s+[А-ЯІЇЄҐA-Z][а-яіїєґ])")


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"^[\s\[\];,.]+|[\s\[\];,.]+$", "", re.sub(r"\s+", " ", value))
    return cleaned or None


def _isbn(value: str) -> str:
    return re.sub(r"\s+", "", value).strip("-")


def _udc(description: str) -> str | None:
    marker = re.search(r"\bУДК\s+", description)
    if marker is None:
        return None
    value = description[marker.end() :]
    value = re.split(r"\s+ББК\s+", value, maxsplit=1)[0]
    leak = INDEX_LEAK.search(value)
    if leak:
        value = value[: leak.start()]
    value = CUTTER.sub("", value)
    return _clean(value)


def parse_bibliographic_details(description: str) -> BibliographicDetails:
    publication = PUBLICATION.search(description)
    physical = PHYSICAL_DESCRIPTION.search(description)
    print_run = PRINT_RUN.search(description)
    catalog = CATALOG_NUMBER.search(description)
    responsibility = RESPONSIBILITY.search(description)
    responsibility_text = responsibility.group(1) if responsibility else ""
    original_title = ORIGINAL_TITLE.search(description)
    translators = TRANSLATORS.search(responsibility_text)
    editors = EDITORS.search(responsibility_text)
    illustrators = ILLUSTRATORS.search(responsibility_text)
    isbns = [_isbn(match.group(1)) for match in DASH_ISBN.finditer(description)]
    return BibliographicDetails(
        responsibility=_clean(responsibility.group(1) if responsibility else None),
        publication_place=_clean(publication.group(1) if publication else None),
        publisher=_clean(publication.group(2) if publication else None),
        physical_description=_clean(physical.group(1) if physical else None),
        print_run=int(print_run.group(1).replace(" ", "")) if print_run else None,
        catalog_number=_clean(catalog.group(1) if catalog else None),
        udc=_udc(description),
        original_title=_clean(original_title.group(1) if original_title else None),
        original_isbn=isbns[1] if len(isbns) > 1 else None,
        translators=_clean(translators.group(1) if translators else None),
        editors=_clean(editors.group(1) if editors else None),
        illustrators=_clean(illustrators.group(1) if illustrators else None),
    )


def primary_isbn(description: str) -> str | None:
    match = DASH_ISBN.search(description)
    return _isbn(match.group(1)) if match else None
