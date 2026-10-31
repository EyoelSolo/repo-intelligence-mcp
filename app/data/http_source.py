"""Bounded HTTP JSON connector for configured data sources."""

import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.data.records import DataRecord, normalize_payload

MAX_RESPONSE_BYTES = 2_000_000
MAX_RECORDS = 1_000


class DataSourceError(RuntimeError):
    """A safe-to-display source configuration or request error."""


class HttpJsonSource:
    def __init__(self, url: str, *, name: str = "configured-source", timeout: float = 15, headers: dict[str, str] | None = None, retries: int = 2, page_param: str | None = None, page_size_param: str | None = None, start_page: int = 1, max_pages: int = 1):
        self.url = url.strip()
        self.name = name
        self.timeout = min(60.0, max(1.0, timeout))
        self.headers = {"Accept": "application/json", **(headers or {})}
        self.retries = min(5, max(0, retries))
        self.page_param = page_param
        self.page_size_param = page_size_param
        self.start_page = max(0, start_page)
        self.max_pages = min(100, max(1, max_pages))

    @classmethod
    def from_environment(cls, url: str) -> "HttpJsonSource":
        """Build a connector using optional JSON request headers from the environment."""
        raw_headers = os.environ.get("REPO_INTELLIGENCE_DATA_HEADERS", "").strip()
        headers: dict[str, str] = {}
        if raw_headers:
            try:
                value = json.loads(raw_headers)
            except json.JSONDecodeError:
                raise DataSourceError("REPO_INTELLIGENCE_DATA_HEADERS must be a JSON object.") from None
            if not isinstance(value, dict) or any(
                not isinstance(key, str) or not isinstance(item, str)
                for key, item in value.items()
            ):
                raise DataSourceError("Data source headers must be string key-value pairs.")
            headers = value
        return cls(url, headers=headers)

    @classmethod
    def configured_sources(cls) -> dict[str, "HttpJsonSource"]:
        """Load named source definitions, falling back to legacy single-source settings."""
        raw = os.environ.get("REPO_INTELLIGENCE_DATA_SOURCES", "").strip()
        if raw:
            try:
                definitions = json.loads(raw)
            except json.JSONDecodeError:
                raise DataSourceError("REPO_INTELLIGENCE_DATA_SOURCES must be a JSON object.") from None
            if not isinstance(definitions, dict) or not definitions:
                raise DataSourceError("REPO_INTELLIGENCE_DATA_SOURCES must contain named source objects.")
            sources = {}
            for name, options in definitions.items():
                if not isinstance(name, str) or not name.strip() or not isinstance(options, dict):
                    raise DataSourceError("Each data source must have a nonempty name and object configuration.")
                url = options.get("url")
                headers = options.get("headers", {})
                if not isinstance(url, str) or not isinstance(headers, dict) or any(
                    not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()
                ):
                    raise DataSourceError(f"Data source '{name}' needs a URL and string header pairs.")
                try:
                    sources[name] = cls(
                        url, name=name,
                        timeout=float(options.get("timeout", 15)),
                        headers=headers,
                        retries=int(options.get("retries", 2)),
                        page_param=options.get("page_param"),
                        page_size_param=options.get("page_size_param"),
                        start_page=int(options.get("start_page", 1)),
                        max_pages=int(options.get("max_pages", 1)),
                    )
                except (TypeError, ValueError):
                    raise DataSourceError(f"Data source '{name}' has invalid numeric or pagination settings.") from None
            return sources
        url = os.environ.get("REPO_INTELLIGENCE_DATA_URL", "").strip()
        return {"configured-source": cls.from_environment(url)} if url else {}

    def fetch(self, *, limit: int = 100) -> list[DataRecord]:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise DataSourceError("Data source URL must be an absolute HTTP or HTTPS URL.")
        limit = min(MAX_RECORDS, max(1, limit))
        records: list[DataRecord] = []
        for offset in range(self.max_pages):
            remaining = limit - len(records)
            page = self.start_page + offset
            url = self.url
            if self.page_param or self.page_size_param:
                from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
                parts = urlsplit(url)
                query = dict(parse_qsl(parts.query, keep_blank_values=True))
                if self.page_param:
                    query[self.page_param] = str(page)
                if self.page_size_param:
                    query[self.page_size_param] = str(min(limit - len(records), MAX_RECORDS))
                url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
            payload = self._request_json(url)
            try:
                batch = normalize_payload(payload, source=self.name, source_url=self.url)
            except ValueError as exc:
                raise DataSourceError(f"Data source returned invalid records: {exc}") from None
            records.extend(batch[:remaining])
            if not batch or len(records) >= limit or (
                self.page_size_param and len(batch) < min(remaining, MAX_RECORDS)
            ):
                break
        return records[:limit]

    def _request_json(self, url: str):
        for attempt in range(self.retries + 1):
            request = Request(url, headers=self.headers)
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise DataSourceError("Data source response exceeded the 2 MB limit.")
                return json.loads(body.decode("utf-8"))
            except HTTPError as exc:
                if exc.code == 429 or 500 <= exc.code < 600:
                    if attempt < self.retries:
                        delay = min(8.0, 0.5 * (2 ** attempt))
                        retry_after = exc.headers.get("Retry-After")
                        try:
                            delay = min(30.0, max(delay, float(retry_after)))
                        except (TypeError, ValueError):
                            try:
                                retry_at = parsedate_to_datetime(retry_after)
                                if retry_at.tzinfo is None:
                                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                                delay = min(30.0, max(delay, (retry_at - datetime.now(timezone.utc)).total_seconds()))
                            except (TypeError, ValueError, OverflowError):
                                pass
                        time.sleep(delay)
                        continue
                    raise DataSourceError(f"Data source returned HTTP {exc.code} after retries.") from None
                raise DataSourceError(f"Data source returned HTTP {exc.code}.") from None
            except (URLError, TimeoutError, OSError):
                if attempt < self.retries:
                    time.sleep(min(8.0, 0.5 * (2 ** attempt)))
                    continue
                raise DataSourceError("Could not reach data source (network error or timeout) after retries.") from None
            except (UnicodeError, json.JSONDecodeError):
                raise DataSourceError("Data source returned invalid UTF-8 JSON.") from None
