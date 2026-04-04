from __future__ import annotations

import json
import re
from collections.abc import Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.core.text import fold_text
from app.pipelines.common.fetcher import fetch_url_text
from app.pipelines.common.processing import normalize_whitespace, parse_datetime
from app.pipelines.common.records import PolicyRecord, SourceDefinition

logger = get_logger(__name__)

DetailFetcher = Callable[[str, SourceDefinition], str]


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


def _extract_meta_content(soup: BeautifulSoup, selector: str) -> str:
    node = soup.select_one(selector)
    return normalize_whitespace(node.get("content")) if node is not None else ""


def _extract_detail_attributes(soup: BeautifulSoup) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in soup.select(".popup__detail--thuoctinh .row"):
        label = normalize_whitespace(row.select_one(".name").get_text(" ", strip=True))
        value_node = row.select_one(".value .child-value") or row.select_one(".value")
        value = normalize_whitespace(value_node.get_text(" ", strip=True) if value_node else None)
        if label and value:
            values[label] = value
    return values


def _guess_policy_field(*parts: str | None) -> str | None:
    joined = fold_text(" ".join(part for part in parts if part))
    keyword_map = {
        "giáo dục": ["giao duc", "hoc sinh", "truong hoc"],
        "y tế": ["y te", "benh vien", "suc khoe"],
        "tài chính": ["tai chinh", "ngan sach", "thue", "phi", "le phi"],
        "giao thông": ["giao thong", "van tai", "duong bo", "duong sat"],
        "quy hoạch": ["quy hoach", "do thi", "dat dai"],
    }
    for field, keywords in keyword_map.items():
        if any(keyword in joined for keyword in keywords):
            return field
    return None


def _extract_doc_number(title: str, attributes: dict[str, str]) -> str | None:
    for key in ("Số ký hiệu", "Ký hiệu"):
        if attributes.get(key):
            return attributes[key]
    match = re.search(r"số\s+([0-9A-Z/\-]+)", title, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _parse_congbao_detail(url: str, payload: str, source: SourceDefinition) -> PolicyRecord | None:
    soup = BeautifulSoup(payload, "html.parser")
    attributes = _extract_detail_attributes(soup)
    title = normalize_whitespace(
        (soup.select_one("h1.title") or soup.select_one("title")).get_text(" ", strip=True)
        if (soup.select_one("h1.title") or soup.select_one("title"))
        else None
    )
    if not title:
        return None

    summary = (
        attributes.get("Trích yếu")
        or _extract_meta_content(soup, "meta[name='description']")
        or _extract_meta_content(soup, "meta[property='og:description']")
    )
    issuing_agency = attributes.get("Cơ quan ban hành")
    field = attributes.get("Lĩnh vực") or _guess_policy_field(title, summary)
    doc_number = _extract_doc_number(title, attributes)
    issued_at = parse_datetime(attributes.get("Ngày ban hành"))
    effective_at = parse_datetime(attributes.get("Ngày hiệu lực"))

    content_parts = [
        title,
        summary,
        f"Số ký hiệu: {doc_number}" if doc_number else None,
        f"Cơ quan ban hành: {issuing_agency}" if issuing_agency else None,
        f"Lĩnh vực: {field}" if field else None,
    ]
    content_clean = normalize_whitespace(". ".join(part for part in content_parts if part)) or None
    default_field = str(source.extra.get("field_default", source.category_default or "chính sách"))
    return PolicyRecord(
        issuing_agency=issuing_agency,
        doc_number=doc_number,
        title=title,
        summary=summary or None,
        content_clean=content_clean,
        field=field or default_field,
        issued_at=issued_at,
        effective_at=effective_at,
        canonical_url=url,
    )


def _parse_congbao_listing(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher,
) -> list[PolicyRecord]:
    soup = BeautifulSoup(payload, "html.parser")
    site_root = str(source.extra.get("site_root") or source.url or "")
    max_items = int(source.extra.get("max_items", 6))
    seen: set[str] = set()
    records: list[PolicyRecord] = []

    for anchor in soup.select("a.sapo[href*='/van-ban/']"):
        href = anchor.get("href")
        if not href:
            continue
        detail_url = urljoin(site_root, href)
        if detail_url in seen:
            continue
        seen.add(detail_url)

        try:
            detail_payload = detail_fetcher(detail_url, source)
            record = _parse_congbao_detail(detail_url, detail_payload, source)
            if record is not None:
                records.append(record)
        except Exception as exc:
            logger.warning("Khong parse duoc van ban %s: %s", detail_url, exc)
            title = normalize_whitespace(anchor.get_text(" ", strip=True))
            if title:
                default_field = str(
                    source.extra.get("field_default", source.category_default or "chính sách")
                )
                records.append(
                    PolicyRecord(
                        issuing_agency=None,
                        doc_number=None,
                        title=title,
                        summary=None,
                        content_clean=title,
                        field=default_field,
                        issued_at=None,
                        effective_at=None,
                        canonical_url=detail_url,
                    )
                )

        if len(records) >= max_items:
            break
    return records


def parse_policy_payload(
    source: SourceDefinition,
    payload: str,
    *,
    detail_fetcher: DetailFetcher | None = None,
) -> list[PolicyRecord]:
    if source.parser == "congbao_listing_html":
        return _parse_congbao_listing(
            source,
            payload,
            detail_fetcher=detail_fetcher or _default_detail_fetcher,
        )

    data = json.loads(payload)
    rows = data.get("records", data if isinstance(data, list) else [])

    records: list[PolicyRecord] = []
    for row in rows:
        records.append(
            PolicyRecord(
                issuing_agency=row.get("issuing_agency"),
                doc_number=row.get("doc_number"),
                title=normalize_whitespace(row.get("title")),
                summary=normalize_whitespace(row.get("summary")),
                content_clean=normalize_whitespace(row.get("content_clean")),
                field=row.get("field"),
                issued_at=parse_datetime(row.get("issued_at")),
                effective_at=parse_datetime(row.get("effective_at")),
                canonical_url=row.get("canonical_url"),
            )
        )
    return [record for record in records if record.title]
