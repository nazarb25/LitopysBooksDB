import pytest

from app.application.dto.book_search import SearchBooksQuery
from app.application.use_cases.issues.import_issue import ImportIssueUseCase
from tests.conftest import ISSUE


def test_import_is_idempotent_and_searches_structured_fields(use_cases) -> None:
    importer, search, _ = use_cases
    first = importer.execute(ISSUE, b"pdf")
    second = importer.execute(ISSUE, b"pdf")

    assert first.books == 1 and not first.skipped
    assert second.skipped
    for query in (
        SearchBooksQuery(author="Кінг С."),
        SearchBooksQuery(publisher="КСД"),
        SearchBooksQuery(publication_place="Харків"),
        SearchBooksQuery(translator="Перекладача"),
        SearchBooksQuery(editor="Редактора"),
        SearchBooksQuery(illustrator="Художника"),
        SearchBooksQuery(original_title="Dark Tower"),
        SearchBooksQuery(original_isbn="1-234"),
        SearchBooksQuery(udc="821.111"),
        SearchBooksQuery(catalog_number="07701"),
        SearchBooksQuery(print_run_min=3000, print_run_max=3000),
        SearchBooksQuery(issue_year=2026, issue_month=8, issue_number=16),
    ):
        assert search.execute(query).total == 1


def test_failed_parse_keeps_existing_data(use_cases) -> None:
    importer, search, _ = use_cases
    importer.execute(ISSUE, b"pdf")

    class BrokenExtractor:
        def extract(self, issue, pdf):
            raise ValueError("incomplete issue")

    broken = ImportIssueUseCase(BrokenExtractor(), importer._uow_factory)
    with pytest.raises(ValueError, match="incomplete"):
        broken.execute(ISSUE, b"changed pdf")
    assert search.execute(SearchBooksQuery(text="Темна вежа")).total == 1


def test_invalid_print_run_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        SearchBooksQuery(print_run_min=5000, print_run_max=1000)


def test_author_search_matches_complete_token(use_cases) -> None:
    importer, search, _ = use_cases
    importer.execute(ISSUE, b"pdf")

    assert search.execute(SearchBooksQuery(author="Кінг")).total == 1
    assert search.execute(SearchBooksQuery(author="Вікінг")).total == 0
