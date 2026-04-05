from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_browser_prefill(
    dataset_title: str,
    *,
    keyword: str = "",
    structured_filters: Mapping[str, str] | None = None,
    sort_label: str = "Mới nhất trước",
) -> dict[str, Any]:
    return {
        "dataset_title": dataset_title,
        "keyword": keyword.strip(),
        "structured_filters": {
            key: value
            for key, value in (structured_filters or {}).items()
            if str(value or "").strip()
        },
        "sort_label": sort_label,
    }


def build_browser_prefill_from_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return build_browser_prefill(
        str(item.get("dataset_title") or "Tin tức"),
        keyword=str(item.get("explorer_keyword") or item.get("title") or "").strip(),
        structured_filters=item.get("explorer_filters") or {},
    )


def build_detail_state(item: Mapping[str, Any], *, origin: str) -> dict[str, Any]:
    return {
        "origin": origin,
        "item": dict(item),
    }


def get_latest_clickable_item(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for message in reversed(messages):
        items = message.get("items") or []
        if items:
            return dict(items[0])
    return None
