from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path

import httpx

from app.core.exceptions import ExternalFetchError
from app.core.logging import get_logger
from app.core.settings import get_settings
from app.pipelines.common.records import FetchResult, SourceDefinition

logger = get_logger(__name__)

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _guess_content_type(source: SourceDefinition) -> str:
    if source.source_type == "rss":
        return "application/rss+xml"
    if source.source_type == "xml":
        return "application/xml"
    if source.source_type == "json":
        return "application/json"
    return "text/html"


def _build_headers(headers: Mapping[str, str] | None = None) -> dict[str, str]:
    merged = dict(DEFAULT_REQUEST_HEADERS)
    if headers:
        merged.update({str(key): str(value) for key, value in headers.items()})
    return merged


def fetch_url_text(
    url: str,
    *,
    timeout_seconds: int,
    retry_count: int,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, object] | None = None,
    method: str = "GET",
    data: Mapping[str, object] | None = None,
    log_name: str | None = None,
) -> FetchResult:
    errors: list[str] = []
    request_name = log_name or url

    for attempt in range(retry_count + 1):
        try:
            response = httpx.request(
                method.upper(),
                url,
                timeout=timeout_seconds,
                follow_redirects=True,
                headers=_build_headers(headers),
                params=params,
                data=data,
            )
            response.raise_for_status()
            logger.info("Fetch thanh cong %s", request_name)
            return FetchResult(
                text=response.text,
                content_type=response.headers.get("content-type"),
                source_url=str(response.url),
                used_demo=False,
            )
        except Exception as exc:
            errors.append(str(exc))
            logger.warning("Fetch that bai %s lan %s: %s", request_name, attempt + 1, exc)
            if attempt < retry_count:
                time.sleep(1.0)

    raise ExternalFetchError(f"Khong the lay du lieu tu {request_name}: {'; '.join(errors)}")


def fetch_source(source: SourceDefinition, *, demo_only: bool = False) -> FetchResult:
    settings = get_settings()
    errors: list[str] = []
    query_params = source.extra.get("query_params")
    request_method = str(source.extra.get("request_method", "GET")).upper()
    form_data = source.extra.get("form_data")

    if not demo_only and source.url:
        try:
            return fetch_url_text(
                source.url,
                timeout_seconds=source.timeout_seconds,
                retry_count=source.retry_count,
                headers=source.headers,
                params=query_params if isinstance(query_params, Mapping) else None,
                method=request_method,
                data=form_data if isinstance(form_data, Mapping) else None,
                log_name=source.name,
            )
        except ExternalFetchError as exc:
            errors.append(str(exc))

    if source.demo_fixture and (demo_only or settings.use_demo_on_failure):
        fixture_path = Path(source.demo_fixture)
        if not fixture_path.is_absolute():
            fixture_path = get_settings().source_config_path.parent.parent / source.demo_fixture
        logger.info("Dung fixture cho %s tai %s", source.name, fixture_path)
        return FetchResult(
            text=fixture_path.read_text(encoding="utf-8"),
            content_type=_guess_content_type(source),
            source_url=source.url,
            used_demo=True,
        )

    message = "; ".join(errors) if errors else "Khong co URL hoac fixture hop le"
    raise ExternalFetchError(f"Khong the lay du lieu tu {source.name}: {message}")
