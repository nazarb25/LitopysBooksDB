import argparse
import json
from typing import Protocol

from app.application.dto.book_search import SearchBooksQuery
from app.application.use_cases.books.backfill_book_details import BackfillBookDetailsUseCase
from app.application.use_cases.books.get_catalog_statistics import GetCatalogStatisticsUseCase
from app.application.use_cases.books.search_books import SearchBooksUseCase
from app.application.use_cases.issues.backfill_issue_months import BackfillIssueMonthsUseCase
from app.application.use_cases.issues.import_issue import ImportIssueUseCase
from app.application.use_cases.issues.sync_catalog import SyncCatalogUseCase
from app.domain.entities import Issue
from app.presentation.api.schemas.books import BookRead


class CliDependencies(Protocol):
    import_issue: ImportIssueUseCase
    sync_catalog: SyncCatalogUseCase
    search_books: SearchBooksUseCase
    get_catalog_statistics: GetCatalogStatisticsUseCase
    backfill_issue_months: BackfillIssueMonthsUseCase
    backfill_book_details: BackfillBookDetailsUseCase


def run_command(args: argparse.Namespace, container: CliDependencies) -> None:
    if args.command == "import-file":
        issue = Issue(args.url, args.year, args.number)
        result = container.import_issue.execute(issue, args.path.read_bytes())
        status = "unchanged" if result.skipped else f"{result.books} records"
        print(f"{issue.year} #{issue.number}: {status}")
    elif args.command == "sync":
        mode = "refresh" if args.refresh else "missing" if args.retry_missing else "new"
        failures = processed = 0
        for position, outcome in enumerate(
            container.sync_catalog.execute(
                since_year=args.since_year,
                limit=args.limit,
                reuse_downloaded=args.reuse_downloaded,
                mode=mode,
            ),
            start=1,
        ):
            processed += 1
            if outcome.error:
                failures += 1
                print(
                    f"[{position}] {outcome.issue.year} #{outcome.issue.number}: "
                    f"ERROR {outcome.error}",
                    flush=True,
                )
            else:
                result = outcome.result
                assert result is not None
                status = "unchanged" if result.skipped else f"{result.books} books"
                print(
                    f"[{position}] {outcome.issue.year} #{outcome.issue.number}: {status}",
                    flush=True,
                )
        if processed == 0:
            message = "Нових випусків немає." if mode == "new" else "Випусків для обробки немає."
            print(message)
        if failures:
            raise SystemExit(f"{failures} issues failed; rerun sync to retry")
    elif args.command == "search":
        values = vars(args)
        query = SearchBooksQuery(
            **{
                name: values[name]
                for name in SearchBooksQuery.__dataclass_fields__
                if name in values
            }
        )
        result = container.search_books.execute(query)
        if args.json:
            print(
                json.dumps(
                    [BookRead.from_dto(book).model_dump() for book in result.items],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for book in result.items:
                issue_date = (
                    f"{book.issue_month:02}.{book.issue_year}"
                    if book.issue_month
                    else str(book.issue_year)
                )
                print(
                    f"{book.title} — {book.author or 'автор не визначений'} "
                    f"({book.publication_year or '?'})"
                )
                print(
                    f"  Літопис № {book.issue_number}, {issue_date}; "
                    f"запис № {book.record_number}; {book.issue_url}#page={book.source_page}"
                )
            print(f"Знайдено: {result.total}")
    elif args.command == "stats":
        statistics = container.get_catalog_statistics.execute()
        print(f"Випусків: {statistics.issues}; записів: {statistics.books}")
    elif args.command == "backfill-months":
        updated, missing = container.backfill_issue_months.execute()
        print(f"Місяць додано до {updated} випусків; без місяця: {missing}")
    elif args.command == "backfill-details":
        updated = container.backfill_book_details.execute()
        print(f"Структуровані поля оновлено для {updated} записів")
