from fastapi.testclient import TestClient

from app.main import create_app
from app.presentation.web.routes import _pagination
from tests.conftest import ISSUE


def test_browser_and_api_search_link_to_source(use_cases) -> None:
    importer, search, _ = use_cases
    importer.execute(ISSUE, b"pdf")
    client = TestClient(create_app(search))

    page = client.get("/", params={"author": "Кінг С."})
    assert page.status_code == 200
    assert "Темна вежа" in page.text
    assert "серпень 2026" in page.text
    assert "Джерело: Літопис книг № 16" in page.text
    assert "Додаткові фільтри" in page.text
    assert "Структуровані дані" in page.text
    assert '<table class="record-table">' in page.text
    assert "Місяць і рік «Літопису»" in page.text
    assert "#page=5" in page.text

    response = client.get("/api/books", params={"author": "Кінг С."})
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["author"] == "Кінг С."
    assert body["items"][0]["issue_month"] == 8
    assert body["total"] == body["page"] == body["pages"] == 1


def test_compact_pagination_keeps_search_parameters() -> None:
    pagination = _pagination(6, 12, {"author": "Кінг", "issue_year": "2025"})

    assert 'aria-current="page">6</span>' in pagination
    assert "…" in pagination
    assert "author=%D0%9A%D1%96%D0%BD%D0%B3" in pagination
    assert "issue_year=2025" in pagination
    assert "page=5" in pagination
    assert "page=7" in pagination
    assert "page=12" in pagination
