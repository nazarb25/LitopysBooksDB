import re
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from litopysdb.domain.models import Issue

CATALOG_URL = "https://ukrbook.net/litopysy.html"
ISSUE_PATH = re.compile(r"/litopys/Knigki/(20\d{2})/[^/?#]+\.pdf$", re.IGNORECASE)
ISSUE_NUMBER = re.compile(r"(?:^|[_-])0*(\d{1,2})(?:[_-](?:20)?\d{2})?\.pdf$", re.IGNORECASE)


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value)


class RemoteSourceError(RuntimeError):
    pass


class BookChamberSource:
    def __init__(self, *, timeout: float = 30, delay: float = 0.5) -> None:
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "LitopysDB/0.1 (personal bibliographic index; polite crawl)"},
        )
        self.delay = delay

    def close(self) -> None:
        self.client.close()

    def _get(self, url: str) -> bytes:
        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                time.sleep(self.delay)
                return response.content
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                if attempt == 2:
                    raise RemoteSourceError(f"Cannot fetch {url}: {exc}") from exc
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    def list_issues(self) -> list[Issue]:
        html = self._get(CATALOG_URL).decode("utf-8", errors="replace")
        parser = _Links()
        parser.feed(html)
        issues: dict[str, Issue] = {}
        for href in parser.hrefs:
            url = urljoin(CATALOG_URL, href)
            parsed = urlparse(url)
            if parsed.hostname not in {"ukrbook.net", "www.ukrbook.net"}:
                continue
            path = parsed.path
            match = ISSUE_PATH.fullmatch(path)
            number = ISSUE_NUMBER.search(path)
            if not match or not number:
                continue
            canonical_url = parsed._replace(query="", fragment="").geturl()
            issues[canonical_url] = Issue(canonical_url, int(match.group(1)), int(number.group(1)))
        if not issues:
            raise RemoteSourceError("No Book Chronicle PDFs found on catalog page")
        return sorted(issues.values(), key=lambda item: (item.year, item.number, item.url))

    def download(self, issue: Issue) -> bytes:
        # Recheck the host so a malformed catalog cannot redirect downloads elsewhere.
        if urlparse(issue.url).hostname not in {"ukrbook.net", "www.ukrbook.net"}:
            raise RemoteSourceError("Unexpected PDF host")
        data = self._get(issue.url)
        if not data.startswith(b"%PDF-"):
            raise RemoteSourceError(f"Response is not a PDF: {issue.url}")
        return data
