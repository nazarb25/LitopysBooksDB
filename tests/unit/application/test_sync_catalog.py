from app.application.dto.issue_import import ImportIssueResultDTO
from app.application.use_cases.issues.sync_catalog import SyncCatalogUseCase
from app.domain.entities import Issue


def test_sync_does_nothing_when_catalog_has_no_new_issue() -> None:
    issue = Issue("https://ukrbook.net/litopys/Knigki/2026/L_k_16_2026.pdf", 2026, 16)

    class Catalog:
        def list_issues(self):
            return [issue]

    class Importer:
        def latest_issue(self):
            return issue

        def has_issue(self, candidate):
            return candidate == issue

        def execute(self, candidate, pdf):
            return ImportIssueResultDTO(candidate, 0, True)

    class UnexpectedIO:
        def download(self, issue):
            raise AssertionError("Indexed issue must not be downloaded")

        def load(self, issue):
            raise AssertionError("Indexed issue must not be loaded")

        def save(self, issue, pdf):
            raise AssertionError("Indexed issue must not be saved")

    io = UnexpectedIO()
    assert list(SyncCatalogUseCase(Catalog(), io, io, Importer()).execute()) == []
