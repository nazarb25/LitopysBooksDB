import argparse
import json
from pathlib import Path

from litopysdb.application.ports import SearchQuery
from litopysdb.application.use_cases import BackfillBookDetails, BackfillIssueMonths, SyncCatalog
from litopysdb.composition import DEFAULT_DB, build_use_cases
from litopysdb.domain.models import Issue
from litopysdb.infrastructure.archive import LocalPdfArchive
from litopysdb.infrastructure.pdf import PyMuPdfExtractor
from litopysdb.infrastructure.source import BookChamberSource
from litopysdb.presentation.schemas import BookRead


def main() -> None:
    parser = argparse.ArgumentParser(prog="litopysdb", description="Book Chronicle bibliography")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    commands = parser.add_subparsers(dest="command", required=True)
    sync = commands.add_parser("sync", help="Download and index newly published issues")
    sync.add_argument("--since-year", type=int)
    sync.add_argument(
        "--limit", type=int, help="Process at most this many issues (for a trial run)"
    )
    sync.add_argument("--pdf-dir", type=Path, default=Path("data/pdfs"))
    sync.add_argument(
        "--reuse-downloaded", action="store_true", help="Use archived PDFs when available"
    )
    sync_mode = sync.add_mutually_exclusive_group()
    sync_mode.add_argument(
        "--retry-missing",
        "--missing-only",
        dest="retry_missing",
        action="store_true",
        help="Retry every issue absent from the database, including older gaps",
    )
    sync_mode.add_argument(
        "--refresh", action="store_true", help="Recheck all listed issues and replace changed PDFs"
    )
    local = commands.add_parser("import-file", help="Index a local PDF")
    local.add_argument("path", type=Path)
    local.add_argument("--year", type=int, required=True)
    local.add_argument("--number", type=int, required=True)
    local.add_argument("--url", required=True, help="Original PDF URL for citation")
    search = commands.add_parser("search", help="Search indexed books")
    search.add_argument("--author")
    search.add_argument("--text")
    search.add_argument("--year", type=int)
    search.add_argument("--issue-year", type=int)
    search.add_argument("--issue-month", type=int)
    search.add_argument("--issue-number", type=int)
    search.add_argument("--publisher")
    search.add_argument("--publication-place")
    search.add_argument("--translator")
    search.add_argument("--editor")
    search.add_argument("--illustrator")
    search.add_argument("--original-title")
    search.add_argument("--isbn")
    search.add_argument("--original-isbn")
    search.add_argument("--udc")
    search.add_argument("--catalog-number")
    search.add_argument("--responsibility")
    search.add_argument("--physical-description")
    search.add_argument("--print-run-min", type=int)
    search.add_argument("--print-run-max", type=int)
    search.add_argument("--limit", type=int, default=50)
    search.add_argument("--offset", type=int, default=0)
    search.add_argument("--json", action="store_true")
    commands.add_parser("stats", help="Show indexed issue and book counts")
    backfill = commands.add_parser(
        "backfill-months", help="Read issue months from archived PDF covers"
    )
    backfill.add_argument("--pdf-dir", type=Path, default=Path("data/pdfs"))
    commands.add_parser(
        "backfill-details", help="Parse structured fields from existing descriptions"
    )
    serve = commands.add_parser("serve", help="Start local browser search")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    importer, finder, uow_factory = build_use_cases(args.db)

    if args.command == "import-file":
        issue = Issue(args.url, args.year, args.number)
        result = importer.execute(issue, args.path.read_bytes())
        print(
            f"{issue.year} #{issue.number}: {'unchanged' if result.skipped else f'{result.books} records'}"
        )
    elif args.command == "sync":
        source = BookChamberSource()
        try:
            syncer = SyncCatalog(source, source, LocalPdfArchive(args.pdf_dir), importer)
            failures = 0
            processed = 0
            for position, outcome in enumerate(
                syncer.execute(
                    since_year=args.since_year,
                    limit=args.limit,
                    reuse_downloaded=args.reuse_downloaded,
                    mode="refresh" if args.refresh else "missing" if args.retry_missing else "new",
                ),
                start=1,
            ):
                processed += 1
                issue = outcome.issue
                if outcome.error:
                    failures += 1
                    print(
                        f"[{position}] {issue.year} #{issue.number}: ERROR {outcome.error}",
                        flush=True,
                    )
                else:
                    result = outcome.result
                    status = "unchanged" if result.skipped else f"{result.books} books"
                    print(f"[{position}] {issue.year} #{issue.number}: {status}", flush=True)
            if processed == 0:
                print(
                    "Нових випусків немає."
                    if not args.refresh and not args.retry_missing
                    else "Випусків для обробки немає."
                )
            if failures:
                raise SystemExit(f"{failures} issues failed; rerun sync to retry")
        finally:
            source.close()
    elif args.command == "search":
        try:
            query = SearchQuery(
                author=args.author,
                text=args.text,
                year=args.year,
                issue_year=args.issue_year,
                issue_month=args.issue_month,
                issue_number=args.issue_number,
                publisher=args.publisher,
                publication_place=args.publication_place,
                translator=args.translator,
                editor=args.editor,
                illustrator=args.illustrator,
                original_title=args.original_title,
                isbn=args.isbn,
                original_isbn=args.original_isbn,
                udc=args.udc,
                catalog_number=args.catalog_number,
                responsibility=args.responsibility,
                physical_description=args.physical_description,
                print_run_min=args.print_run_min,
                print_run_max=args.print_run_max,
                limit=args.limit,
                offset=args.offset,
            )
        except ValueError as exc:
            parser.error(str(exc))
        books = finder.execute(query)
        if args.json:
            print(
                json.dumps(
                    [BookRead.from_book(book).model_dump() for book in books],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for book in books:
                print(
                    f"{book.title} — {book.author or 'автор не визначений'} ({book.publication_year or '?'})"
                )
                issue_date = (
                    f"{book.issue_month:02}.{book.issue_year}"
                    if book.issue_month
                    else str(book.issue_year or "?")
                )
                print(
                    f"  Літопис № {book.issue_number}, {issue_date}; "
                    f"запис № {book.record_number}; {book.issue_url}#page={book.source_page}"
                )
            print(f"Знайдено: {len(books)}")
    elif args.command == "stats":
        with uow_factory() as uow:
            print(f"Випусків: {uow.books.count_issues()}; записів: {uow.books.count_books()}")
    elif args.command == "backfill-months":
        updated, missing = BackfillIssueMonths(
            PyMuPdfExtractor(), LocalPdfArchive(args.pdf_dir), uow_factory
        ).execute()
        print(f"Місяць додано до {updated} випусків; без місяця: {missing}")
    elif args.command == "backfill-details":
        updated = BackfillBookDetails(uow_factory).execute()
        print(f"Структуровані поля оновлено для {updated} записів")
    elif args.command == "serve":
        import uvicorn

        from litopysdb.presentation.web import create_app

        uvicorn.run(create_app(finder), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
