from __future__ import annotations

from collections.abc import Mapping
from html import unescape
from typing import Any

DATASET_TITLE_BY_KIND = {
    "news": "Tin tức",
    "policy": "Chính sách",
    "traffic": "Giao thông",
    "price": "Giá cả",
    "weather": "Thời tiết",
}
DATASET_KEY_TO_KIND = {
    "articles": "news",
    "price_snapshots": "price",
    "weather_snapshots": "weather",
    "policy_documents": "policy",
    "traffic_events": "traffic",
}


def shorten_preview_text(value: Any, limit: int = 180) -> str:
    if value is None:
        return ""
    clean_value = " ".join(unescape(str(value)).split())
    if len(clean_value) <= limit:
        return clean_value
    return clean_value[: max(limit - 1, 0)].rstrip() + "…"


def infer_item_kind(item: Mapping[str, Any]) -> str | None:
    if "item_name" in item or "display_value" in item:
        return "price"
    if "forecast_time" in item or "weather_text" in item:
        return "weather"
    if "event_type" in item or "description" in item or "url" in item:
        return "traffic"
    if "issuing_agency" in item or "doc_number" in item or "issued_at" in item:
        return "policy"
    if "published_at" in item or "content_clean" in item or "category" in item:
        return "news"
    return None


def build_content_item(kind: str, item: Mapping[str, Any]) -> dict[str, Any]:
    if kind == "news":
        title = str(item.get("title") or "Bản tin chưa có tiêu đề")
        summary = shorten_preview_text(
            item.get("summary") or item.get("content_clean") or "Chưa có tóm tắt cho bản tin này.",
            limit=220,
        )
        source = str(item.get("source") or item.get("source_name") or "unknown")
        metadata = {
            "category": str(item.get("category") or ""),
            "published_at": str(item.get("published_at") or ""),
            "content_clean": shorten_preview_text(item.get("content_clean"), limit=320),
        }
        return {
            "kind": "news",
            "internal_id": item.get("id"),
            "title": title,
            "summary": summary,
            "source": source,
            "url": item.get("canonical_url"),
            "updated_at": item.get("published_at"),
            "action_type": "detail",
            "dataset_title": DATASET_TITLE_BY_KIND["news"],
            "explorer_keyword": title,
            "explorer_filters": {
                "source_name": source,
                "pipeline_name": "news",
            },
            "question_hint": f"Tóm tắt ngắn gọn bài viết này: {title}",
            "metadata": metadata,
        }

    if kind == "policy":
        title = str(item.get("title") or "Văn bản chưa có tiêu đề")
        summary = shorten_preview_text(
            item.get("summary")
            or item.get("content_clean")
            or "Hiện hệ thống mới có phần mô tả ngắn cho văn bản này.",
            limit=220,
        )
        source = str(item.get("source") or item.get("source_name") or "unknown")
        metadata = {
            "issuing_agency": str(item.get("issuing_agency") or ""),
            "doc_number": str(item.get("doc_number") or ""),
            "field": str(item.get("field") or ""),
            "issued_at": str(item.get("issued_at") or ""),
            "effective_at": str(item.get("effective_at") or ""),
            "content_clean": shorten_preview_text(item.get("content_clean"), limit=320),
        }
        return {
            "kind": "policy",
            "internal_id": item.get("id"),
            "title": title,
            "summary": summary,
            "source": source,
            "url": item.get("canonical_url"),
            "updated_at": item.get("issued_at") or item.get("effective_at"),
            "action_type": "detail",
            "dataset_title": DATASET_TITLE_BY_KIND["policy"],
            "explorer_keyword": title,
            "explorer_filters": {
                "source_name": source,
                "pipeline_name": "policy",
            },
            "question_hint": f"Tóm tắt nhanh văn bản này: {title}",
            "metadata": metadata,
        }

    if kind == "traffic":
        title = str(item.get("title") or "Sự kiện giao thông chưa có tiêu đề")
        summary = shorten_preview_text(
            item.get("description")
            or "Hiện chưa có mô tả chi tiết hơn cho sự kiện giao thông này.",
            limit=220,
        )
        source = str(item.get("source") or item.get("source_name") or "unknown")
        location = str(item.get("location") or "")
        metadata = {
            "event_type": str(item.get("event_type") or ""),
            "location": location,
            "start_time": str(item.get("start_time") or ""),
            "end_time": str(item.get("end_time") or ""),
        }
        return {
            "kind": "traffic",
            "internal_id": item.get("id"),
            "title": title,
            "summary": summary,
            "source": source,
            "url": item.get("url"),
            "updated_at": item.get("start_time") or item.get("end_time"),
            "action_type": "detail",
            "dataset_title": DATASET_TITLE_BY_KIND["traffic"],
            "explorer_keyword": title,
            "explorer_filters": {
                "source_name": source,
                "pipeline_name": "traffic",
                "location": location or "Tất cả",
            },
            "question_hint": f"Tóm tắt nhanh sự kiện giao thông này: {title}",
            "metadata": metadata,
        }

    if kind == "price":
        display_name = str(
            item.get("display_name") or item.get("item_name") or "Bản ghi giá chưa rõ tên"
        )
        display_value = (
            item.get("display_value")
            or item.get("display_sell_price")
            or item.get("sell_price")
            or item.get("display_buy_price")
            or item.get("buy_price")
            or "Chưa có giá"
        )
        source = str(item.get("source") or item.get("source_name") or "unknown")
        region = str(item.get("region") or "")
        metadata = {
            "item_name": str(item.get("item_name") or ""),
            "item_type": str(item.get("item_type") or ""),
            "region": region,
            "unit": str(item.get("display_unit") or item.get("unit") or ""),
            "buy_price": str(item.get("display_buy_price") or item.get("buy_price") or ""),
            "sell_price": str(item.get("display_sell_price") or item.get("sell_price") or ""),
            "effective_at": str(item.get("effective_at") or ""),
        }
        summary_parts = [str(display_value)]
        if region:
            summary_parts.append(f"Khu vực: {region}")
        if metadata["unit"]:
            summary_parts.append(str(metadata["unit"]))
        return {
            "kind": "price",
            "internal_id": item.get("id"),
            "title": display_name,
            "summary": " · ".join(part for part in summary_parts if part),
            "source": source,
            "url": None,
            "updated_at": item.get("effective_at"),
            "action_type": "detail",
            "dataset_title": DATASET_TITLE_BY_KIND["price"],
            "explorer_keyword": str(item.get("item_name") or display_name),
            "explorer_filters": {
                "source_name": source,
                "pipeline_name": "price",
                "item_name": str(item.get("item_name") or ""),
            },
            "question_hint": f"Giải thích nhanh mức giá hiện tại của {display_name}",
            "metadata": metadata,
        }

    if kind == "weather":
        location = str(item.get("location") or "Địa điểm chưa rõ")
        weather_text = str(item.get("weather_text") or "Chưa có mô tả thời tiết")
        warning_text = str(item.get("warning_text") or "")
        temp_text = (
            f"{item.get('min_temp', '?')} - {item.get('max_temp', '?')}°C"
            if item.get("min_temp") is not None or item.get("max_temp") is not None
            else "Chưa có nhiệt độ"
        )
        source = str(item.get("source") or item.get("source_name") or "unknown")
        summary_parts = [temp_text, weather_text]
        if warning_text:
            summary_parts.append(warning_text)
        metadata = {
            "humidity": str(item.get("humidity") or ""),
            "wind": str(item.get("wind") or ""),
            "forecast_time": str(item.get("forecast_time") or ""),
            "warning_text": warning_text,
        }
        return {
            "kind": "weather",
            "internal_id": item.get("id"),
            "title": location,
            "summary": " · ".join(part for part in summary_parts if part),
            "source": source,
            "url": None,
            "updated_at": item.get("forecast_time") or item.get("updated_at"),
            "action_type": "detail",
            "dataset_title": DATASET_TITLE_BY_KIND["weather"],
            "explorer_keyword": location,
            "explorer_filters": {
                "source_name": source,
                "pipeline_name": "weather",
                "location": location,
            },
            "question_hint": f"Tóm tắt nhanh thời tiết tại {location}",
            "metadata": metadata,
        }

    raise ValueError(f"Không hỗ trợ loại item: {kind}")


def extract_content_items(payload: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []

    raw_items = payload.get("items")
    if isinstance(raw_items, list) and raw_items:
        normalized_items: list[dict[str, Any]] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, Mapping):
                continue
            kind = infer_item_kind(raw_item)
            if not kind:
                continue
            normalized_items.append(build_content_item(kind, raw_item))
        if normalized_items:
            return normalized_items

    current = payload.get("current")
    if isinstance(current, Mapping):
        item_name = payload.get("item_name")
        display_name = payload.get("display_name")
        return [
            build_content_item(
                "price",
                {
                    "id": None,
                    "item_name": item_name,
                    "display_name": display_name,
                    "display_value": current.get("display_value"),
                    "display_buy_price": current.get("display_buy_price"),
                    "display_sell_price": current.get("display_sell_price"),
                    "buy_price": current.get("buy_price"),
                    "sell_price": current.get("sell_price"),
                    "unit": current.get("unit"),
                    "display_unit": current.get("display_unit"),
                    "effective_at": current.get("effective_at"),
                    "source": current.get("source"),
                },
            )
        ]

    if payload.get("location") and payload.get("weather_text"):
        return [build_content_item("weather", payload)]

    return []


def build_content_item_from_dataset_record(
    dataset_key: str,
    record: Mapping[str, Any],
) -> dict[str, Any] | None:
    kind = DATASET_KEY_TO_KIND.get(dataset_key)
    if not kind:
        return None

    if kind == "news":
        return build_content_item(
            "news",
            {
                "id": record.get("id"),
                "title": record.get("title"),
                "summary": record.get("summary"),
                "content_clean": record.get("content_clean"),
                "category": record.get("category"),
                "published_at": record.get("published_at"),
                "canonical_url": record.get("canonical_url"),
                "source": record.get("source_name"),
            },
        )

    if kind == "policy":
        return build_content_item(
            "policy",
            {
                "id": record.get("id"),
                "title": record.get("title"),
                "summary": record.get("summary"),
                "content_clean": record.get("content_clean"),
                "field": record.get("field"),
                "issuing_agency": record.get("issuing_agency"),
                "doc_number": record.get("doc_number"),
                "issued_at": record.get("issued_at"),
                "effective_at": record.get("effective_at"),
                "canonical_url": record.get("canonical_url"),
                "source": record.get("source_name"),
            },
        )

    if kind == "traffic":
        return build_content_item(
            "traffic",
            {
                "id": record.get("id"),
                "title": record.get("title"),
                "event_type": record.get("event_type"),
                "location": record.get("location"),
                "start_time": record.get("start_time"),
                "end_time": record.get("end_time"),
                "description": record.get("description"),
                "url": record.get("url"),
                "source": record.get("source_name"),
            },
        )

    if kind == "price":
        return build_content_item(
            "price",
            {
                "id": record.get("id"),
                "item_name": record.get("item_name"),
                "item_type": record.get("item_type"),
                "region": record.get("region"),
                "buy_price": record.get("buy_price"),
                "sell_price": record.get("sell_price"),
                "unit": record.get("unit"),
                "effective_at": record.get("effective_at"),
                "source": record.get("source_name"),
            },
        )

    if kind == "weather":
        return build_content_item(
            "weather",
            {
                "id": record.get("id"),
                "location": record.get("location"),
                "forecast_time": record.get("forecast_time"),
                "min_temp": record.get("min_temp"),
                "max_temp": record.get("max_temp"),
                "humidity": record.get("humidity"),
                "wind": record.get("wind"),
                "weather_text": record.get("weather_text"),
                "warning_text": record.get("warning_text"),
                "source": record.get("source_name"),
            },
        )

    return None
