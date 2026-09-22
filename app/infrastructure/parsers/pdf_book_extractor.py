import re

import pymupdf

from app.application.dto.issue_import import ExtractedIssueDTO
from app.domain.entities import Book, Issue
from app.infrastructure.parsers.bibliography_parser import (
    parse_bibliographic_details,
    primary_isbn,
)

RECORD_START = re.compile(r"^\s*(\d{1,6})(?:(\.)\s*|\s+)(.+)$")
RECORD_RANGE = re.compile(r"\((\d{1,6})\s*[—–-]\s*(\d{1,6})\)")
INDEX_HEADING = re.compile(
    r"^(?:ПЕРЕЛІК МОВ|ІМЕННИЙ ПОКАЖЧИК|ПРЕДМЕТНИЙ ПОКАЖЧИК|ПОКАЖЧИК НАЗВ|ГЕОГРАФІЧНИЙ ПОКАЖЧИК)",
    re.IGNORECASE,
)
AUTHOR_HEADING = re.compile(
    r"^([А-ЯІЇЄҐЁA-Z][А-Яа-яІіЇїЄєҐґЁёA-Za-z’'\-]+,?\s+(?:[А-ЯІЇЄҐЁA-Z]\.?\s*){1,3})\s+(.+)$"
)
ISBN = re.compile(r"[ІI]SBN\s*([0-9XХxх][0-9XХxх\-\s]{8,24}[0-9XХxх])", re.IGNORECASE)
PUB_YEAR = re.compile(r"(?:,|\s)(1[89]\d{2}|20\d{2})\s*[.р]?(?:\s*[—–-]|\s*\.)")
MONTHS = (
    "січень",
    "лютий",
    "березень",
    "квітень",
    "травень",
    "червень",
    "липень",
    "серпень",
    "вересень",
    "жовтень",
    "листопад",
    "грудень",
)
ISSUE_MONTH = re.compile(
    r"\b(" + "|".join(MONTHS) + r")\s*,?\s*(20\d{2})\b",
    re.IGNORECASE,
)


def _month_from_cover(text: str, year: int) -> int | None:
    # A 2008 cover begins "Cерпень" with a Latin C.
    text = re.sub(r"\b[Cc](?=ерпень)", "с", text)
    for match in ISSUE_MONTH.finditer(text):
        if int(match.group(2)) == year:
            return MONTHS.index(match.group(1).casefold()) + 1
    return None


def _normalize(text: str) -> str:
    text = re.sub(r"(?<=[А-Яа-яІіЇїЄєҐґ])-\s*\n\s*(?=[а-яіїєґ])", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _book(issue: Issue, number: int, page: int, raw: str) -> Book:
    description = _normalize(raw)
    author = None
    body = description
    heading = AUTHOR_HEADING.match(description)
    if heading:
        author, body = heading.groups()
        author = author.strip(" ,.")
        body = re.sub(r"^\([^)]*\)\.\s*", "", body)
    title = re.split(r"\s+/\s+|\s+[—–]\s+", body, maxsplit=1)[0].strip(" .;:")
    if not title:
        title = body[:150].strip()
    if author is None:
        responsibility = re.search(r"\s/\s([^;.—]{3,100})", description)
        if responsibility:
            candidate = responsibility.group(1).strip(" []")
            # The responsibility statement can name an editor or translator; only take a clear name.
            if re.fullmatch(r"[А-ЯІЇЄҐЁA-Z][\w’'\-]+(?:\s+[А-ЯІЇЄҐЁA-Z][\w’'\-]+){1,2}", candidate):
                author = candidate
    isbn_match = ISBN.search(description)
    isbn = primary_isbn(description)
    if isbn is None and isbn_match:
        isbn = re.sub(r"\s+", "", isbn_match.group(1)).strip("-")
    pub_year = PUB_YEAR.search(description)
    return Book(
        issue_url=issue.url,
        record_number=number,
        title=title,
        description=description,
        source_page=page,
        author=author,
        isbn=isbn,
        publication_year=int(pub_year.group(1)) if pub_year else None,
        details=parse_bibliographic_details(description),
    )


class PyMuPdfBookExtractor:
    def extract_month(self, issue: Issue, pdf: bytes) -> int | None:
        with pymupdf.open(stream=pdf, filetype="pdf") as document:
            return _month_from_cover(document[0].get_text(), issue.year)

    def extract(self, issue: Issue, pdf: bytes, *, tolerant: bool = False) -> ExtractedIssueDTO:
        records: list[Book] = []
        current_number: int | None = None
        maximum_number: int | None = None
        seen: set[int] = set()
        current_page = 0
        current_lines: list[str] = []

        def finish() -> ExtractedIssueDTO:
            if current_number is not None:
                records.append(_book(issue, current_number, current_page, "\n".join(current_lines)))
            records.sort(key=lambda book: book.record_number)
            if expected_start is not None and expected_end is not None:
                expected_count = expected_end - expected_start + 1
                missing = expected_count - len(records)
                if missing and not tolerant:
                    return self.extract(issue, pdf, tolerant=True)
                if not records or missing > max(5, expected_count // 100):
                    raise ValueError(
                        f"Incomplete issue {issue.year} #{issue.number}: "
                        f"parsed {len(records)} of {expected_count} records"
                    )
            elif not tolerant:
                return self.extract(issue, pdf, tolerant=True)
            return ExtractedIssueDTO(tuple(records), month)

        with pymupdf.open(stream=pdf, filetype="pdf") as document:
            month = _month_from_cover(document[0].get_text(), issue.year)
            cover = RECORD_RANGE.search(document[0].get_text())
            expected_start = int(cover.group(1)) if cover else None
            expected_end = int(cover.group(2)) if cover else None
            body_start = None
            for page in list(document)[3:9]:
                for line in page.get_text(sort=True).splitlines():
                    first = re.match(r"^\s{3,}(\d{1,6})\.\s+\S", line)
                    if first:
                        body_start = int(first.group(1))
                        break
                if body_start is not None:
                    break
            if body_start is not None and body_start != expected_start:
                # A few published PDFs have a cover copied from another issue.
                expected_start = body_start
                expected_end = None
            for page_number, page in enumerate(document, start=1):
                for line in page.get_text(sort=True).splitlines():
                    if current_number is not None and INDEX_HEADING.match(line.strip()):
                        return finish()
                    match = RECORD_START.match(line)
                    if match:
                        number = int(match.group(1))
                        # Old issues contain small numbering gaps and occasionally swap adjacent records.
                        if (
                            current_number is None and number == expected_start and match.group(2)
                        ) or (
                            current_number is not None
                            and number not in seen
                            and (
                                number == current_number + 1
                                if not tolerant
                                else (
                                    expected_start is not None
                                    and maximum_number is not None
                                    and expected_start
                                    <= number
                                    <= (expected_end or expected_start + 5000)
                                    and maximum_number - 10 <= number <= maximum_number + 10
                                )
                            )
                        ):
                            if current_number is not None:
                                records.append(
                                    _book(
                                        issue,
                                        current_number,
                                        current_page,
                                        "\n".join(current_lines),
                                    )
                                )
                            current_number = number
                            maximum_number = max(maximum_number or number, number)
                            seen.add(number)
                            current_page = page_number
                            current_lines = [match.group(3)]
                            continue
                    if current_number is not None and line.strip() != str(page_number):
                        current_lines.append(line)
        return finish()
