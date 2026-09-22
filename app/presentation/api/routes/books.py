from fastapi import APIRouter, HTTPException, Query

from app.application.dto.book_search import SearchBooksQuery
from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.presentation.api.schemas.books import BookRead, SearchResponse


def create_books_router(search_books: SearchBooksUseCase) -> APIRouter:
    router = APIRouter(prefix="/api/books", tags=["books"])

    @router.get("", response_model=SearchResponse)
    def books(
        author: str | None = None,
        text: str | None = None,
        year: int | None = None,
        issue_year: int | None = None,
        issue_month: int | None = Query(None, ge=1, le=12),
        issue_number: int | None = Query(None, ge=1),
        publisher: str | None = None,
        publication_place: str | None = None,
        translator: str | None = None,
        editor: str | None = None,
        illustrator: str | None = None,
        original_title: str | None = None,
        isbn: str | None = None,
        original_isbn: str | None = None,
        udc: str | None = None,
        catalog_number: str | None = None,
        responsibility: str | None = None,
        physical_description: str | None = None,
        print_run_min: int | None = Query(None, ge=0),
        print_run_max: int | None = Query(None, ge=0),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> SearchResponse:
        try:
            query = SearchBooksQuery(
                author=author,
                text=text,
                year=year,
                issue_year=issue_year,
                issue_month=issue_month,
                issue_number=issue_number,
                publisher=publisher,
                publication_place=publication_place,
                translator=translator,
                editor=editor,
                illustrator=illustrator,
                original_title=original_title,
                isbn=isbn,
                original_isbn=original_isbn,
                udc=udc,
                catalog_number=catalog_number,
                responsibility=responsibility,
                physical_description=physical_description,
                print_run_min=print_run_min,
                print_run_max=print_run_max,
                limit=limit,
                offset=offset,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        result = search_books.execute(query)
        return SearchResponse(
            items=[BookRead.from_dto(item) for item in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            page=result.page,
            pages=result.pages,
        )

    return router
