from pathlib import Path
from typing import Protocol

from app.application.dto.database_snapshot import (
    DatabaseDownloadDTO,
    DatabaseSnapshotDTO,
)


class DatabaseSnapshotService(Protocol):
    def create(self, database_path: Path, output_directory: Path) -> DatabaseSnapshotDTO: ...

    def download(
        self,
        *,
        archive_url: str,
        checksum_url: str,
        database_path: Path,
        force: bool,
    ) -> DatabaseDownloadDTO: ...
