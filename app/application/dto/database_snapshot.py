from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatabaseSnapshotDTO:
    archive_path: Path
    checksum_path: Path
    metadata_path: Path
    sha256: str
    compressed_size: int
    issues: int
    books: int


@dataclass(frozen=True, slots=True)
class DatabaseDownloadDTO:
    database_path: Path
    sha256: str
    compressed_size: int
