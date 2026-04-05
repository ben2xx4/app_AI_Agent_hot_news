from __future__ import annotations

from app.core.content_items import (
    build_content_item,
    build_content_item_from_dataset_record,
    extract_content_items,
)


def test_extract_content_items_builds_news_cards() -> None:
    payload = {
        "items": [
            {
                "id": 1,
                "title": "Tin hot tại TP.HCM",
                "summary": "Có diễn biến mới trong ngày.",
                "published_at": "2026-04-05T08:00:00",
                "canonical_url": "https://example.com/news-1",
                "source": "vnexpress_rss_tin_moi",
                "category": "thoi-su",
            }
        ]
    }

    items = extract_content_items(payload)

    assert len(items) == 1
    assert items[0]["kind"] == "news"
    assert items[0]["dataset_title"] == "Tin tức"
    assert items[0]["explorer_filters"]["pipeline_name"] == "news"


def test_build_content_item_for_price_contains_item_filter() -> None:
    item = build_content_item(
        "price",
        {
            "id": 4,
            "item_name": "gia-vang-sjc",
            "display_name": "Giá vàng SJC",
            "display_value": "174.500.000 VNĐ/lượng",
            "effective_at": "2026-04-05T03:50:00",
            "source": "sjc_gold_prices_live",
        },
    )

    assert item["kind"] == "price"
    assert item["explorer_filters"]["item_name"] == "gia-vang-sjc"
    assert "174.500.000" in item["summary"]


def test_build_content_item_from_dataset_record_maps_articles() -> None:
    item = build_content_item_from_dataset_record(
        "articles",
        {
            "id": 7,
            "title": "Bài viết mới",
            "summary": "Tóm tắt ngắn",
            "content_clean": "Noi dung day du",
            "category": "giao-duc",
            "published_at": "2026-04-05T09:30:00",
            "canonical_url": "https://example.com/a7",
            "source_name": "thanhnien_rss_giao_duc",
        },
    )

    assert item is not None
    assert item["kind"] == "news"
    assert item["source"] == "thanhnien_rss_giao_duc"
