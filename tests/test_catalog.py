from litopysdb.infrastructure.source import BookChamberSource


def test_catalog_filters_book_pdfs_and_handles_old_names(monkeypatch):
    html = b"""<a href="litopys/Knigki/2004/L_K_1_04.pdf">1</a>
    <a href="/litopys/Knigki/2026/L_k_16_2026.pdf">16</a>
    <a href="/litopys/Statti/2026/L_s_1_2026.pdf">article</a>
    <a href="https://evil.example/litopys/Knigki/2026/L_k_2_2026.pdf">evil</a>"""
    source = BookChamberSource(delay=0)
    monkeypatch.setattr(source, "_get", lambda _: html)
    try:
        issues = source.list_issues()
    finally:
        source.close()
    assert [(issue.year, issue.number) for issue in issues] == [(2004, 1), (2026, 16)]
