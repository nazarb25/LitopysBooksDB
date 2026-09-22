import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import httpx
import zstandard

from app.application.dto.database_snapshot import (
    DatabaseDownloadDTO,
    DatabaseSnapshotDTO,
)


class SqliteZstandardSnapshotService:
    ARCHIVE_NAME = "litopys.db.zst"

    def create(self, database_path: Path, output_directory: Path) -> DatabaseSnapshotDTO:
        output_directory.mkdir(parents=True, exist_ok=True)
        backup_path = output_directory / ".litopys.snapshot.db"
        archive_path = output_directory / self.ARCHIVE_NAME
        temporary_archive = archive_path.with_suffix(".zst.tmp")
        checksum_path = output_directory / f"{self.ARCHIVE_NAME}.sha256"
        metadata_path = output_directory / "dataset.json"

        try:
            with (
                closing(sqlite3.connect(database_path)) as source,
                closing(sqlite3.connect(backup_path)) as target,
            ):
                source.backup(target)
            metadata = self._metadata(backup_path)
            compressor = zstandard.ZstdCompressor(level=10, threads=-1)
            with backup_path.open("rb") as source, temporary_archive.open("wb") as target:
                compressor.copy_stream(source, target)
            temporary_archive.replace(archive_path)
        finally:
            backup_path.unlink(missing_ok=True)
            temporary_archive.unlink(missing_ok=True)

        digest = self._sha256(archive_path)
        checksum_path.write_text(f"{digest}  {self.ARCHIVE_NAME}\n")
        metadata.update(
            {
                "archive": self.ARCHIVE_NAME,
                "compressed_bytes": archive_path.stat().st_size,
                "sha256": digest,
                "generated_at": datetime.now(UTC).isoformat(),
                "source": "https://www.ukrbook.net/litopysy.html",
                "pdf_files_included": False,
            }
        )
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return DatabaseSnapshotDTO(
            archive_path=archive_path,
            checksum_path=checksum_path,
            metadata_path=metadata_path,
            sha256=digest,
            compressed_size=archive_path.stat().st_size,
            issues=metadata["issues"],
            books=metadata["books"],
        )

    def download(
        self,
        *,
        archive_url: str,
        checksum_url: str,
        database_path: Path,
        force: bool,
    ) -> DatabaseDownloadDTO:
        if database_path.exists() and not force:
            raise FileExistsError(
                f"Database already exists: {database_path}. Use --force to replace it."
            )
        database_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path = database_path.with_suffix(".db.zst.download")
        temporary_database = database_path.with_suffix(".db.download")
        try:
            with httpx.stream("GET", archive_url, follow_redirects=True, timeout=120) as response:
                response.raise_for_status()
                with archive_path.open("wb") as target:
                    for chunk in response.iter_bytes():
                        target.write(chunk)
            checksum_response = httpx.get(checksum_url, follow_redirects=True, timeout=30)
            checksum_response.raise_for_status()
            expected_digest = checksum_response.text.split(maxsplit=1)[0].lower()
            actual_digest = self._sha256(archive_path)
            if actual_digest != expected_digest:
                raise ValueError("Downloaded database checksum does not match")

            decompressor = zstandard.ZstdDecompressor()
            with archive_path.open("rb") as source, temporary_database.open("wb") as target:
                decompressor.copy_stream(source, target)
            self._verify_database(temporary_database)
            temporary_database.replace(database_path)
            return DatabaseDownloadDTO(
                database_path=database_path,
                sha256=actual_digest,
                compressed_size=archive_path.stat().st_size,
            )
        finally:
            archive_path.unlink(missing_ok=True)
            temporary_database.unlink(missing_ok=True)

    @staticmethod
    def _metadata(database_path: Path) -> dict[str, int | str | None]:
        with closing(sqlite3.connect(database_path)) as connection:
            issues = connection.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
            books = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
            first_year, last_year = connection.execute(
                "SELECT MIN(year), MAX(year) FROM issues"
            ).fetchone()
            has_alembic = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'alembic_version'"
            ).fetchone()
            revision = (
                connection.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
                if has_alembic
                else None
            )
        return {
            "issues": issues,
            "books": books,
            "first_issue_year": first_year,
            "last_issue_year": last_year,
            "schema_revision": revision[0] if revision else None,
        }

    @staticmethod
    def _verify_database(database_path: Path) -> None:
        with closing(sqlite3.connect(database_path)) as connection:
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
        if integrity != "ok" or not {"issues", "books"}.issubset(tables):
            raise ValueError("Downloaded database failed integrity validation")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()
