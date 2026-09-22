import pytest

from app.domain.entities import Book, Issue
from app.domain.exceptions import InvalidBibliographicRecordError


def test_issue_requires_an_http_pdf_url() -> None:
    with pytest.raises(InvalidBibliographicRecordError):
        Issue("file:///issue.pdf", 2026, 1)


def test_book_requires_positive_record_and_page_numbers() -> None:
    with pytest.raises(InvalidBibliographicRecordError):
        Book("https://example.com/issue.pdf", 0, "Title", "Description", 1)
