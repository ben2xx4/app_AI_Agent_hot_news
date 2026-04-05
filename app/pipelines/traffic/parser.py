from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.core.text import fold_text
from app.core.traffic_rules import is_relevant_traffic_content
from app.pipelines.common.fetcher import fetch_url_text
from app.pipelines.common.processing import (
    is_datetime_within_age_window,
    normalize_whitespace,
    parse_datetime,
)
from app.pipelines.common.records import SourceDefinition, TrafficRecord

logger = get_logger(__name__)

DetailFetcher = Callable[[str, SourceDefinition], str]
NowProvider = Callable[[], datetime]


def _default_detail_fetcher(url: str, source: SourceDefinition) -> str:
    timeout_seconds = int(source.extra.get("detail_timeout_seconds", source.timeout_seconds))
    retry_count = int(source.extra.get("detail_retry_count", source.retry_count))
    result = fetch_url_text(
        url,
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        headers=source.headers,
        log_name=f"{source.name}:detail",
    )
    return result.text


def _guess_location(source: SourceDefinition, *parts: str | None) -> str | None:
    haystack = fold_text(" ".join(part for part in parts if part))
    keyword_map = source.extra.get("location_keywords") or {
        "Hà Nội": ["ha noi", "tran khac chan", "dai co viet", "nguyen khoai"],
        "TP.HCM": ["tp hcm", "sai gon", "ho chi minh"],
        "Đà Nẵng": ["da nang"],
    }
    for location, keywords in keyword_map.items():
        if any(fold_text(str(keyword)) in haystack for keyword in keywords):
            return str(location)
    return source.extra.get("default_location")


def _guess_event_type(*parts: str | None) -> str:
    haystack = fold_text(" ".join(part for part in parts if part))
    if any(keyword in haystack for keyword in ["tai nan", "truot nga", "va cham"]):
        return "tai_nan"
    if any(keyword in haystack for keyword in ["un tac", "ket xe", "dong xe"]):
        return "un_tac"
    if any(keyword in haystack for keyword in ["phan luong", "cam duong", "han che"]):
        return "phan_luong"
    return "cap_nhat_giao_thong"


def _parse_vov_detail(url: str, payload: str, source: SourceDefinition) -> TrafficRecord | None:
    soup = BeautifulSoup(payload, "html.parser")
    title_node = soup.select_one("h1.the-article-title") or soup.select_one(
        "meta[property='og:title']"
    )
    title = normalize_whitespace(
        title_node.get_text(" ", strip=True) if title_node and title_node.name != "meta" else None
    ) or normalize_whitespace(title_node.get("content") if title_node else None)
    if not title:
        return None

    summary_node = soup.select_one("h2.sapo") or soup.select_one("meta[property='og:description']")
    summary = normalize_whitespace(
        summary_node.get_text(" ", strip=True)
        if summary_node and summary_node.name != "meta"
        else None
    ) or normalize_whitespace(summary_node.get("content") if summary_node else None)

    content_root = soup.select_one("#content_detail-photo") or soup.select_one(
        ".main-content-photo"
    )
    paragraphs: list[str] = []
    if content_root is not None:
        for paragraph in content_root.select("p"):
            if paragraph.find_parent("figcaption") is not None:
                continue
            text = normalize_whitespace(paragraph.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)

    match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', payload)
    start_time = parse_datetime(match.group(1)) if match else None
    description = "\n".join(paragraphs) if paragraphs else summary
    if not is_relevant_traffic_content(title, summary, description):
        return None

    return TrafficRecord(
        event_type=_guess_event_type(title, summary, description),
        title=title,
        location=_guess_location(source, title, summary, description),
        start_time=start_time,
        end_time=None,
        description=description,
        url=url,
    )


def _parse_vov_listing(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher,
    now_provider: NowProvider,
) -> list[TrafficRecord]:
    soup = BeautifulSoup(payload, "html.parser")
    site_root = str(source.extra.get("site_root") or source.url or "")
    max_items = int(source.extra.get("max_items", 8))
    seen: set[str] = set()
    records: list[TrafficRecord] = []

    for anchor in soup.select("a[href*='/newsaudio/']"):
        href = anchor.get("href")
        if not href:
            continue
        detail_url = urljoin(site_root, href)
        if detail_url in seen:
            continue
        seen.add(detail_url)

        try:
            detail_payload = detail_fetcher(detail_url, source)
            record = _parse_vov_detail(detail_url, detail_payload, source)
            if record is not None and is_datetime_within_age_window(
                record.start_time,
                source.extra.get("max_age_days"),
                now_provider=now_provider,
            ):
                records.append(record)
        except Exception as exc:
            logger.warning("Khong parse duoc tin giao thong %s: %s", detail_url, exc)

        if len(records) >= max_items:
            break
    return records


def _parse_vnexpress_detail(
    url: str,
    payload: str,
    source: SourceDefinition,
) -> TrafficRecord | None:
    soup = BeautifulSoup(payload, "html.parser")
    title_meta = soup.select_one("meta[property='og:title']")
    title_node = soup.select_one("h1.title-detail, h1")
    title_meta_text = normalize_whitespace(title_meta.get("content") if title_meta else None)
    title_node_text = normalize_whitespace(
        title_node.get_text(" ", strip=True) if title_node else None
    )
    title = title_meta_text or title_node_text
    if not title:
        return None

    summary_meta = soup.select_one("meta[property='og:description']") or soup.select_one(
        "meta[name='description']"
    )
    summary_node = soup.select_one("p.description")
    summary_meta_text = normalize_whitespace(summary_meta.get("content") if summary_meta else None)
    summary_node_text = normalize_whitespace(
        summary_node.get_text(" ", strip=True) if summary_node else None
    )
    summary = summary_meta_text or summary_node_text

    content_root = soup.select_one("article.fck_detail") or soup.select_one(".fck_detail")
    paragraphs: list[str] = []
    if content_root is not None:
        for paragraph in content_root.select("p.Normal"):
            if paragraph.find_parent("figcaption") is not None:
                continue
            text = normalize_whitespace(paragraph.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)

    published_meta = soup.select_one("meta[name='pubdate']") or soup.select_one(
        "meta[itemprop='datePublished']"
    )
    description = "\n".join(paragraphs) if paragraphs else summary
    if not is_relevant_traffic_content(title, summary, description):
        return None

    return TrafficRecord(
        event_type=_guess_event_type(title, summary, description),
        title=title,
        location=_guess_location(source, title, summary, description),
        start_time=parse_datetime(published_meta.get("content")) if published_meta else None,
        end_time=None,
        description=description,
        url=url,
    )


def _parse_vnexpress_listing(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher,
    now_provider: NowProvider,
) -> list[TrafficRecord]:
    soup = BeautifulSoup(payload, "html.parser")
    site_root = str(source.extra.get("site_root") or source.url or "")
    max_items = int(source.extra.get("max_items", 12))
    seen: set[str] = set()
    records: list[TrafficRecord] = []

    for anchor in soup.select("article.item-news h2.title-news a[href]"):
        href = normalize_whitespace(anchor.get("href"))
        if not href:
            continue
        detail_url = urljoin(site_root, href).split("#", 1)[0]
        if detail_url in seen:
            continue
        seen.add(detail_url)

        try:
            detail_payload = detail_fetcher(detail_url, source)
            record = _parse_vnexpress_detail(detail_url, detail_payload, source)
            if record is not None and is_datetime_within_age_window(
                record.start_time,
                source.extra.get("max_age_days"),
                now_provider=now_provider,
            ):
                records.append(record)
        except Exception as exc:
            logger.warning("Khong parse duoc tin giao thong VnExpress %s: %s", detail_url, exc)

        if len(records) >= max_items:
            break
    return records


def parse_traffic_payload(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher | None = None,
    now_provider: NowProvider | None = None,
) -> list[TrafficRecord]:
    effective_now_provider = now_provider or (lambda: datetime.now(UTC))
    if source.parser == "vov_listing_html":
        return _parse_vov_listing(
            source,
            payload,
            detail_fetcher=detail_fetcher or _default_detail_fetcher,
            now_provider=effective_now_provider,
        )
    if source.parser == "vnexpress_listing_html":
        return _parse_vnexpress_listing(
            source,
            payload,
            detail_fetcher=detail_fetcher or _default_detail_fetcher,
            now_provider=effective_now_provider,
        )

    data = json.loads(payload)
    rows = data.get("records", data if isinstance(data, list) else [])
    records: list[TrafficRecord] = []
    for row in rows:
        records.append(
            TrafficRecord(
                event_type=row.get("event_type"),
                title=normalize_whitespace(row.get("title")),
                location=row.get("location"),
                start_time=parse_datetime(row.get("start_time")),
                end_time=parse_datetime(row.get("end_time")),
                description=normalize_whitespace(row.get("description")),
                url=row.get("url"),
            )
        )
    return [
        record
        for record in records
        if record.title
        and is_datetime_within_age_window(
            record.start_time,
            source.extra.get("max_age_days"),
            now_provider=effective_now_provider,
        )
    ]
