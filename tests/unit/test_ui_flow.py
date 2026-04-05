from __future__ import annotations

from app.ui.flow import (
    build_browser_prefill,
    build_browser_prefill_from_item,
    get_latest_clickable_item,
)


def test_build_browser_prefill_keeps_filters() -> None:
    payload = build_browser_prefill(
        "Tin tức",
        keyword="TP.HCM",
        structured_filters={"pipeline_name": "news", "source_name": "vnexpress_rss_tin_moi"},
    )

    assert payload["dataset_title"] == "Tin tức"
    assert payload["keyword"] == "TP.HCM"
    assert payload["structured_filters"]["pipeline_name"] == "news"


def test_build_browser_prefill_from_item_uses_item_context() -> None:
    payload = build_browser_prefill_from_item(
        {
            "dataset_title": "Giao thông",
            "title": "Cấm đường tại trung tâm",
            "explorer_keyword": "Cấm đường tại trung tâm",
            "explorer_filters": {"pipeline_name": "traffic", "location": "TP.HCM"},
        }
    )

    assert payload["dataset_title"] == "Giao thông"
    assert payload["structured_filters"]["location"] == "TP.HCM"


def test_get_latest_clickable_item_returns_latest_assistant_item() -> None:
    messages = [
        {"role": "assistant", "items": []},
        {"role": "assistant", "items": [{"title": "Tin đầu", "kind": "news"}]},
        {"role": "user", "items": []},
        {"role": "assistant", "items": [{"title": "Tin mới hơn", "kind": "news"}]},
    ]

    item = get_latest_clickable_item(messages)

    assert item is not None
    assert item["title"] == "Tin mới hơn"
