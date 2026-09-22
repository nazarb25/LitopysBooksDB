from dataclasses import replace
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.application.dto.book_search import SearchBooksQuery
from app.application.use_cases.books.search_books import SearchBooksUseCase

MONTH_NAMES = (
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

STYLE = """<style>
body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#202429}
form{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr) auto;gap:.8rem;align-items:end;margin:1.5rem 0}
fieldset{min-width:0;margin:0;padding:.6rem .7rem .7rem;border:1px solid #c8d0da;border-radius:8px}
legend{padding:0 .3rem;font-size:.9rem;font-weight:650;color:#58636e}
.fields{display:grid;gap:.5rem}.search-fields .fields{grid-template-columns:repeat(2,minmax(0,1fr))}
.filter-fields .fields{grid-template-columns:repeat(4,minmax(0,1fr))}
label{display:grid;gap:.25rem;min-width:0;font-size:.8rem;color:#58636e}
input,select,button{box-sizing:border-box;width:100%;font:inherit;padding:.55rem;border:1px solid #aab3be;border-radius:6px}
button{width:auto;background:#164d84;color:white;cursor:pointer}article{padding:1rem 0;border-top:1px solid #ddd}
small{color:#58636e}.source{display:block;margin-top:.35rem;color:#384b5f;font-weight:600}a{color:#164d84}p{line-height:1.5}
details{margin-top:.8rem;border:1px solid #d6dce3;border-radius:7px;background:#fafbfc}
summary{padding:.65rem .8rem;color:#164d84;font-weight:650;cursor:pointer;user-select:none}
.record-table{width:100%;border-collapse:collapse;background:white}.record-table th,.record-table td{padding:.55rem .8rem;border-top:1px solid #e2e6ea;text-align:left;vertical-align:top}
.record-table th{width:28%;color:#58636e;font-weight:600}.record-table td{overflow-wrap:anywhere}
.advanced-filters{grid-column:1/-1;margin:0}.advanced-filters summary{color:#384b5f}.advanced-fields{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;padding:.2rem .8rem .8rem}
.result-count{color:#58636e}.pagination{display:flex;align-items:center;justify-content:center;gap:.3rem;flex-wrap:wrap;margin:1.5rem 0}
.pagination a,.pagination span{display:inline-flex;min-width:2.2rem;height:2.2rem;box-sizing:border-box;align-items:center;justify-content:center;padding:0 .55rem;border:1px solid #c8d0da;border-radius:6px;text-decoration:none}
.pagination .current{border-color:#164d84;background:#164d84;color:white;font-weight:700}.pagination .disabled{color:#98a1ab;background:#f5f6f7}.pagination .ellipsis{border:0;min-width:auto;padding:0 .2rem}
@media(max-width:800px){form{grid-template-columns:1fr}.filter-fields .fields,.advanced-fields{grid-template-columns:repeat(2,minmax(0,1fr))}button{width:100%}}
@media(max-width:450px){.search-fields .fields,.filter-fields .fields,.advanced-fields{grid-template-columns:1fr}}
</style>"""


def _pagination(current: int, pages: int, params: dict[str, str]) -> str:
    if pages <= 1:
        return ""

    def link(label: str, target: int, *, current_page: bool = False) -> str:
        if current_page:
            return f'<span class="current" aria-current="page">{label}</span>'
        href = urlencode({**params, "page": target})
        return f'<a href="/?{escape(href, quote=True)}">{label}</a>'

    items = [
        link("«", 1) if current > 1 else '<span class="disabled">«</span>',
        link("‹", current - 1) if current > 1 else '<span class="disabled">‹</span>',
    ]
    visible = set(range(max(1, current - 2), min(pages, current + 2) + 1)) | {1, pages}
    previous = 0
    for number in sorted(visible):
        if previous and number > previous + 1:
            items.append('<span class="ellipsis">…</span>')
        items.append(link(str(number), number, current_page=number == current))
        previous = number
    items.extend(
        [
            link("›", current + 1) if current < pages else '<span class="disabled">›</span>',
            link("»", pages) if current < pages else '<span class="disabled">»</span>',
        ]
    )
    return '<nav class="pagination" aria-label="Сторінки">' + "".join(items) + "</nav>"


def create_web_router(search_books: SearchBooksUseCase) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def home(
        author: str = "",
        text: str = "",
        year: str = "",
        issue_year: str = "",
        issue_month: str = "",
        issue_number: str = "",
        publisher: str = "",
        publication_place: str = "",
        translator: str = "",
        editor: str = "",
        illustrator: str = "",
        original_title: str = "",
        isbn: str = "",
        original_isbn: str = "",
        udc: str = "",
        catalog_number: str = "",
        responsibility: str = "",
        physical_description: str = "",
        print_run_min: str = "",
        print_run_max: str = "",
        page: int = Query(1, ge=1),
    ) -> str:
        search_fields = "".join(
            f'<label>{label}<input name="{name}" value="{escape(value, quote=True)}" '
            f'placeholder="{placeholder}"></label>'
            for name, label, placeholder, value in (
                ("author", "Автор", "Кінг С.", author),
                ("text", "Назва або текст", "Назва книги", text),
            )
        )
        filter_fields = "".join(
            f'<label>{label}<input name="{name}" type="number" min="{minimum}" max="2100" '
            f'value="{escape(value, quote=True)}" placeholder="Рік"></label>'
            for name, label, minimum, value in (
                ("year", "Рік книги", 1400, year),
                ("issue_year", "Рік Літопису", 1924, issue_year),
            )
        )
        month_options = '<option value="">Місяць випуску Літопису</option>' + "".join(
            f'<option value="{number}"{" selected" if issue_month == str(number) else ""}>{name.capitalize()}</option>'
            for number, name in enumerate(MONTH_NAMES, start=1)
        )
        filter_fields += (
            f'<label>Місяць Літопису<select name="issue_month">{month_options}</select></label>'
        )
        filter_fields += (
            f'<label>Номер Літопису<input name="issue_number" type="number" min="1" '
            f'value="{escape(issue_number, quote=True)}" placeholder="№"></label>'
        )
        criteria = (
            f'<fieldset class="search-fields"><legend>Пошук</legend><div class="fields">'
            f"{search_fields}</div></fieldset>"
            f'<fieldset class="filter-fields"><legend>Фільтри</legend><div class="fields">'
            f"{filter_fields}</div></fieldset>"
        )
        advanced_values = (
            ("publisher", "Видавництво", publisher),
            ("publication_place", "Місце видання", publication_place),
            ("translator", "Перекладач", translator),
            ("editor", "Редактор", editor),
            ("illustrator", "Ілюстратор / художник", illustrator),
            ("original_title", "Назва оригіналу", original_title),
            ("isbn", "ISBN книги", isbn),
            ("original_isbn", "ISBN оригіналу", original_isbn),
            ("udc", "УДК", udc),
            ("catalog_number", "Реєстраційний номер", catalog_number),
            ("responsibility", "Відомості про відповідальність", responsibility),
            ("physical_description", "Фізичний опис", physical_description),
        )
        advanced_fields = "".join(
            f'<label>{label}<input name="{name}" value="{escape(value, quote=True)}"></label>'
            for name, label, value in advanced_values
        )
        advanced_fields += (
            f'<label>Тираж від<input name="print_run_min" type="number" min="0" '
            f'value="{escape(print_run_min, quote=True)}"></label>'
            f'<label>Тираж до<input name="print_run_max" type="number" min="0" '
            f'value="{escape(print_run_max, quote=True)}"></label>'
        )
        active_advanced = (
            sum(bool(value) for _, _, value in advanced_values)
            + bool(print_run_min)
            + bool(print_run_max)
        )
        advanced_filters = (
            f'<details class="advanced-filters"{" open" if active_advanced else ""}>'
            f"<summary>Додаткові фільтри"
            f"{' (' + str(active_advanced) + ')' if active_advanced else ''}</summary>"
            f'<div class="advanced-fields">{advanced_fields}</div></details>'
        )
        content = "<p>Пошук працює за автором і назвою; результати можна звузити за роком книги, роком, місяцем і номером випуску Літопису.</p>"
        if any(
            (
                author,
                text,
                year,
                issue_year,
                issue_month,
                issue_number,
                *(value for _, _, value in advanced_values),
                print_run_min,
                print_run_max,
            )
        ):
            try:
                query = SearchBooksQuery(
                    author=author or None,
                    text=text or None,
                    year=int(year) if year else None,
                    issue_year=int(issue_year) if issue_year else None,
                    issue_month=int(issue_month) if issue_month else None,
                    issue_number=int(issue_number) if issue_number else None,
                    publisher=publisher or None,
                    publication_place=publication_place or None,
                    translator=translator or None,
                    editor=editor or None,
                    illustrator=illustrator or None,
                    original_title=original_title or None,
                    isbn=isbn or None,
                    original_isbn=original_isbn or None,
                    udc=udc or None,
                    catalog_number=catalog_number or None,
                    responsibility=responsibility or None,
                    physical_description=physical_description or None,
                    print_run_min=int(print_run_min) if print_run_min else None,
                    print_run_max=int(print_run_max) if print_run_max else None,
                    offset=(page - 1) * 50,
                )
                result = search_books.execute(query)
                total = result.total
                pages = result.pages
                current_page = min(page, pages) if pages else 1
                if current_page != page:
                    query = replace(query, offset=(current_page - 1) * query.limit)
                    result = search_books.execute(query)
                found = result.items
                cards = []
                for book in found:
                    link = escape(f"{book.issue_url}#page={book.source_page}", quote=True)
                    issue_date = (
                        f"{MONTH_NAMES[book.issue_month - 1]} {book.issue_year}"
                        if book.issue_month and book.issue_year
                        else str(book.issue_year or "дата невідома")
                    )
                    structured_rows = (
                        ("Назва", book.title),
                        ("Автор", book.author or "Не визначено"),
                        ("Відомості про відповідальність", book.details.responsibility),
                        ("Перекладачі", book.details.translators),
                        ("Редактори", book.details.editors),
                        ("Ілюстратори / художники", book.details.illustrators),
                        ("Місце видання", book.details.publication_place),
                        ("Видавництво", book.details.publisher),
                        ("Рік видання книги", book.publication_year or "Не визначено"),
                        ("Фізичний опис", book.details.physical_description),
                        (
                            "Тираж",
                            f"{book.details.print_run:,} прим.".replace(",", " ")
                            if book.details.print_run
                            else None,
                        ),
                        ("ISBN", book.isbn or "Не визначено"),
                        ("Назва оригіналу", book.details.original_title),
                        ("ISBN оригіналу", book.details.original_isbn),
                        ("УДК", book.details.udc),
                        ("Реєстраційний номер", book.details.catalog_number),
                        ("Номер бібліографічного запису", book.record_number),
                        ("Номер «Літопису книг»", book.issue_number or "Не визначено"),
                        ("Місяць і рік «Літопису»", issue_date),
                        ("Сторінка PDF", book.source_page),
                    )
                    structured_table = "".join(
                        f"<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>"
                        for label, value in structured_rows
                        if value is not None
                    )
                    cards.append(
                        f"<article><h2>{escape(book.title)}</h2>"
                        f"<small>{escape(book.author or 'Автор не визначений')} · "
                        f"рік видання книги: {book.publication_year or 'невідомий'} · "
                        f"запис № {book.record_number}</small>"
                        f'<small class="source">Джерело: Літопис книг № {book.issue_number}, '
                        f"{issue_date}</small>"
                        f"<p>{escape(book.description)}</p>"
                        f'<a href="{link}" target="_blank" rel="noopener">Відкрити PDF, с. {book.source_page}</a>'
                        f'<details><summary>Структуровані дані</summary><table class="record-table">'
                        f"{structured_table}</table></details></article>"
                    )
                params = {
                    "author": author,
                    "text": text,
                    "year": year,
                    "issue_year": issue_year,
                    "issue_month": issue_month,
                    "issue_number": issue_number,
                    **{name: value for name, _, value in advanced_values},
                    "print_run_min": print_run_min,
                    "print_run_max": print_run_max,
                }
                page_label = f"Сторінка {current_page} з {pages}" if pages else "Сторінок немає"
                navigation = _pagination(current_page, pages, params)
                content = (
                    f'<p class="result-count">Знайдено: {total:,} · {page_label}</p>'.replace(
                        ",", " "
                    )
                    + navigation
                    + "".join(cards)
                    + navigation
                )
            except ValueError:
                content = "<p>Перевірте рік і місяць у фільтрі.</p>"
        return f'<!doctype html><html lang="uk"><meta charset="utf-8"><title>Літопис книг</title>{STYLE}<h1>Літопис книг</h1><form>{criteria}<button>Шукати</button>{advanced_filters}</form>{content}</html>'

    return router
