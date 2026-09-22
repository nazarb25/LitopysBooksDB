import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1] / "app"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [
        (
            "domain",
            {
                "app.application",
                "app.infrastructure",
                "app.presentation",
                "sqlalchemy",
                "fastapi",
                "pydantic",
                "httpx",
                "pymupdf",
            },
        ),
        (
            "application",
            {
                "app.infrastructure",
                "app.presentation",
                "sqlalchemy",
                "fastapi",
                "pydantic",
                "httpx",
                "pymupdf",
            },
        ),
        ("presentation", {"app.infrastructure"}),
    ],
)
def test_layer_import_boundaries(layer: str, forbidden: set[str]) -> None:
    violations: list[str] = []
    for path in (ROOT / layer).rglob("*.py"):
        for module in imported_modules(path):
            if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden):
                violations.append(f"{path.relative_to(ROOT)} imports {module}")
    assert not violations, "\n".join(violations)
