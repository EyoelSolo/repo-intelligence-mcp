"""Bounded HTTP JSON connector for configured data sources."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.data.records import DataRecord, normalize_payload

MAX_RESPONSE_BYTES = 2_000_000
MAX_RECORDS = 1_000


class DataSourceError(RuntimeError):
    """A safe-to-display source configuration or request error."""


class HttpJsonSource:
    def __init__(self, url: str, *, name: str = "configured-source", timeout: float = 15):
        self.url = url.strip()
        self.name = name
        self.timeout = min(60.0, max(1.0, timeout))

    def fetch(self, *, limit: int = 100) -> list[DataRecord]:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise DataSourceError("Data source URL must be an absolute HTTP or HTTPS URL.")
        limit = min(MAX_RECORDS, max(1, limit))
        request = Request(self.url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            raise DataSourceError(f"Data source returned HTTP {exc.code}.") from None
        except (URLError, TimeoutError, OSError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            raise DataSourceError(f"Could not reach data source: {reason}") from None

        if len(body) > MAX_RESPONSE_BYTES:
            raise DataSourceError("Data source response exceeded the 2 MB limit.")
        try:
            payload = json.loads(body.decode("utf-8"))
            records = normalize_payload(payload, source=self.name, source_url=self.url)
        except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise DataSourceError(f"Data source returned invalid JSON records: {exc}") from None
        return records[:limit]
