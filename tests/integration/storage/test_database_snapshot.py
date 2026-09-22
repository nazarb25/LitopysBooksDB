import hashlib
import json
import sqlite3
from pathlib import Path

import zstandard

from app.infrastructure.storage.sqlite_zstandard_snapshot import (
    SqliteZstandardSnapshotService,
)
from tests.conftest import ISSUE


def test_snapshot_is_consistent_and_self_describing(use_cases, tmp_path: Path) -> None:
    importer, _, _ = use_cases
    importer.execute(ISSUE, b"pdf")
    database_path = tmp_path / "books.db"
    output_directory = tmp_path / "release"

    result = SqliteZstandardSnapshotService().create(database_path, output_directory)

    digest = hashlib.sha256(result.archive_path.read_bytes()).hexdigest()
    assert digest == result.sha256
    assert result.checksum_path.read_text().startswith(digest)
    metadata = json.loads(result.metadata_path.read_text())
    assert metadata["issues"] == 1
    assert metadata["books"] == 1
    assert metadata["pdf_files_included"] is False

    restored = tmp_path / "restored.db"
    decompressor = zstandard.ZstdDecompressor()
    with result.archive_path.open("rb") as source, restored.open("wb") as target:
        decompressor.copy_stream(source, target)
    with sqlite3.connect(restored) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 1
