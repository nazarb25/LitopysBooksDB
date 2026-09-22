from fastapi.testclient import TestClient
from test_import_search import ISSUE, _cases

from litopysdb.presentation.web import _pagination, create_app


def test_browser_and_api_search_link_to_source(tmp_path):
    importer, finder, _ = _cases(tmp_path / "books.db")
    importer.execute(ISSUE, b"pdf")
    client = TestClient(create_app(finder))
    page = client.get("/", params={"author": "Кінг С."})
    assert page.status_code == 200
    assert "Темна вежа" in page.text
    assert "<legend>Пошук</legend>" in page.text
    assert "<legend>Фільтри</legend>" in page.text
    assert "серпень 2026" in page.text
    assert "Джерело: Літопис книг № 16" in page.text
    assert "Номер Літопису" in page.text
    assert "Додаткові фільтри" in page.text
    assert "Перекладач" in page.text
    assert "Назва оригіналу" in page.text
    assert "Структуровані дані" in page.text
    assert '<table class="record-table">' in page.text
    assert "Номер бібліографічного запису" in page.text
    assert "Місяць і рік «Літопису»" in page.text
    assert "978-617-123-456-7" in page.text
    assert "#page=5" in page.text
    response = client.get("/api/books", params={"author": "Кінг С."})
    assert response.status_code == 200
    assert response.json()["items"][0]["author"] == "Кінг С."
    assert response.json()["items"][0]["issue_month"] == 8
    assert response.json()["total"] == 1
    assert response.json()["page"] == 1
    assert response.json()["pages"] == 1
    filtered = client.get(
        "/api/books", params={"issue_year": 2026, "issue_month": 8, "issue_number": 16}
    )
    assert len(filtered.json()["items"]) == 1
    absent = client.get("/api/books", params={"issue_year": 2026, "issue_month": 7})
    assert absent.json()["items"] == []
    assert absent.json()["total"] == 0
    assert absent.json()["pages"] == 0

    advanced = client.get(
        "/",
        params={"publisher": "КСД", "translator": "Перекладача", "print_run_min": 3000},
    )
    assert "Темна вежа" in advanced.text
    assert '<details class="advanced-filters" open>' in advanced.text
    assert "Додаткові фільтри (3)" in advanced.text
    filtered_api = client.get(
        "/api/books",
        params={"original_title": "Dark Tower", "original_isbn": "1-234"},
    )
    assert filtered_api.json()["total"] == 1


def test_compact_pagination_keeps_search_parameters():
    pagination = _pagination(6, 12, {"author": "Кінг", "issue_year": "2025"})

    assert 'aria-label="Сторінки"' in pagination
    assert 'aria-current="page">6</span>' in pagination
    assert "…" in pagination
    assert "author=%D0%9A%D1%96%D0%BD%D0%B3" in pagination
    assert "issue_year=2025" in pagination
    assert "page=5" in pagination
    assert "page=7" in pagination
    assert "page=12" in pagination
