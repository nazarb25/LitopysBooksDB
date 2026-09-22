import argparse
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="litopysdb", description="Book Chronicle bibliography")
    parser.add_argument("--db", type=Path, help="SQLite database path")
    parser.add_argument("--pdf-dir", type=Path, help="Downloaded PDF directory")
    commands = parser.add_subparsers(dest="command", required=True)

    sync = commands.add_parser("sync", help="Download and index newly published issues")
    sync.add_argument("--since-year", type=int)
    sync.add_argument("--limit", type=int, help="Process at most this many issues")
    sync.add_argument("--reuse-downloaded", action="store_true")
    sync_mode = sync.add_mutually_exclusive_group()
    sync_mode.add_argument("--retry-missing", "--missing-only", action="store_true")
    sync_mode.add_argument("--refresh", action="store_true")

    local = commands.add_parser("import-file", help="Index a local PDF")
    local.add_argument("path", type=Path)
    local.add_argument("--year", type=int, required=True)
    local.add_argument("--number", type=int, required=True)
    local.add_argument("--url", required=True)

    search = commands.add_parser("search", help="Search indexed books")
    for name in (
        "author",
        "text",
        "publisher",
        "publication-place",
        "translator",
        "editor",
        "illustrator",
        "original-title",
        "isbn",
        "original-isbn",
        "udc",
        "catalog-number",
        "responsibility",
        "physical-description",
    ):
        search.add_argument(f"--{name}")
    for name in (
        "year",
        "issue-year",
        "issue-month",
        "issue-number",
        "print-run-min",
        "print-run-max",
        "limit",
        "offset",
    ):
        search.add_argument(
            f"--{name}",
            type=int,
            default=50 if name == "limit" else 0 if name == "offset" else None,
        )
    search.add_argument("--json", action="store_true")

    commands.add_parser("stats", help="Show indexed issue and book counts")
    commands.add_parser("backfill-months", help="Read issue months from PDF covers")
    commands.add_parser("backfill-details", help="Parse structured bibliographic fields")
    commands.add_parser("db-upgrade", help="Apply database migrations")
    download = commands.add_parser("db-download", help="Download the latest database snapshot")
    download.add_argument("--force", action="store_true", help="Replace an existing database")
    snapshot = commands.add_parser("snapshot", help="Create release assets from the database")
    snapshot.add_argument("--output-dir", type=Path, default=Path("dist/data"))
    serve = commands.add_parser("serve", help="Start local browser search")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    return parser
