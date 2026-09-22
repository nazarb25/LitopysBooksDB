from pathlib import Path

from app.application.dto.database_snapshot import DatabaseSnapshotDTO
from app.application.interfaces.services.database_snapshot import DatabaseSnapshotService


class CreateDatabaseSnapshotUseCase:
    def __init__(self, service: DatabaseSnapshotService, database_path: Path) -> None:
        self._service = service
        self._database_path = database_path

    def execute(self, output_directory: Path) -> DatabaseSnapshotDTO:
        if not self._database_path.is_file():
            raise FileNotFoundError(f"Database does not exist: {self._database_path}")
        return self._service.create(self._database_path, output_directory)
