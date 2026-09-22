from pathlib import Path

from litopysdb.domain.models import Issue


class LocalPdfArchive:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def _path(self, issue: Issue) -> Path:
        return self.folder / str(issue.year) / f"{issue.number:02}.pdf"

    def load(self, issue: Issue) -> bytes | None:
        path = self._path(issue)
        return path.read_bytes() if path.exists() else None

    def save(self, issue: Issue, pdf: bytes) -> None:
        path = self._path(issue)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_bytes(pdf)
        temporary.replace(path)
