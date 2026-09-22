from pathlib import Path

from app.application.dto.database_snapshot import DatabaseDownloadDTO
from app.application.interfaces.services.database_snapshot import DatabaseSnapshotService


class DownloadDatabaseSnapshotUseCase:
    def __init__(
        self,
        service: DatabaseSnapshotService,
        database_path: Path,
        archive_url: str,
    ) -> None:
        self._service = service
        self._database_path = database_path
        self._archive_url = archive_url

    def execute(self, *, force: bool = False) -> DatabaseDownloadDTO:
        return self._service.download(
            archive_url=self._archive_url,
            checksum_url=f"{self._archive_url}.sha256",
            database_path=self._database_path,
            force=force,
        )
