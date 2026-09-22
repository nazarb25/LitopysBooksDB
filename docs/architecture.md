# Architecture and decisions

## Understanding

- Search across every available issue of **Літопис книг**, initially listed from 2004 onward on the Book Chamber page.
- Index individual bibliographic records so author, title, year, ISBN and original description can be queried.
- Keep a direct reference to the PDF and page for every result.
- Store data locally for one user, with no accounts or remote deployment.
- Permit a long first import; repeat imports must be idempotent and failures recoverable per issue.
- Other Chronicle series are outside this first version.

## Decision log

| Decision | Alternative | Reason |
| --- | --- | --- |
| SQLite through SQLAlchemy | JSON files, PostgreSQL | Queryable and durable without a server; can replace adapter later. |
| Python 3.14 and uv | System Python and pip | Requested stack and reproducible dependency lock. |
| PyMuPDF text extraction | OCR on all pages | The sample and inspected early PDFs contain text; OCR should be added only for scanned issues. |
| Strict author field plus full description | Name-index-only search | Name indexes also contain editors, translators and subjects. |
| CLI plus local FastAPI search | Public hosted site | Useful immediately, private by default, minimal operation. |
| Per-issue transaction and SHA-256 | Full rebuild each run | Safe re-import and resume after individual failures. |

## Placement

| Component | Layer | Role |
| --- | --- | --- |
| `Issue`, `Book`, invariants | Domain | Bibliographic identity and validity |
| `ImportIssue`, `SearchBooks`, ports | Application | Import and query scenarios |
| `BookChamberSource`, `PyMuPdfExtractor` | Infrastructure | Remote HTTP and PDF adapters |
| SQLAlchemy rows, repository, Unit of Work | Infrastructure | Durable storage and transactions |
| CLI, FastAPI, Pydantic response | Presentation | User input and output |
| `composition.py` | Composition root | Dependency wiring |

The import use case calculates the checksum, extracts records outside a database transaction, then replaces one issue and commits once. A parser or network error leaves the previous issue data intact. Domain and application never import SQLAlchemy, Pydantic, FastAPI or PyMuPDF. The CLI maps per-issue errors to visible failures while continuing with other issues. Search uses SQL filtering and bounded result sets.
