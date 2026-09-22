from fastapi import FastAPI

from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.bootstrap.container import create_container
from app.presentation.api.routes.books import create_books_router
from app.presentation.web.routes import create_web_router


def create_app(search_books: SearchBooksUseCase | None = None) -> FastAPI:
    if search_books is None:
        search_books = create_container().search_books
    application = FastAPI(title="Літопис книг — пошук")
    application.include_router(create_books_router(search_books))
    application.include_router(create_web_router(search_books))
    return application
