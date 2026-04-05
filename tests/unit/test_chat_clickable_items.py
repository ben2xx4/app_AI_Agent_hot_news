from __future__ import annotations

from datetime import datetime

from app.models import Article
from app.services.chat_service import ChatService


def test_chat_service_hot_news_returns_clickable_items(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Tin hot hôm nay là gì?")

    assert payload["items"]
    first_item = payload["items"][0]
    assert first_item["kind"] == "news"
    assert first_item["dataset_title"] == "Tin tức"
    assert first_item["title"]


def test_chat_service_can_summarize_context_item(seeded_db) -> None:
    context_item = {
        "kind": "news",
        "title": "Tin hot tại TP.HCM",
        "summary": "Có diễn biến mới trong ngày.",
        "source": "vnexpress_rss_tin_moi",
        "url": "https://example.com/news-1",
        "updated_at": "2026-04-05T08:00:00",
        "dataset_title": "Tin tức",
        "action_type": "detail",
        "explorer_keyword": "Tin hot tại TP.HCM",
        "explorer_filters": {"pipeline_name": "news", "source_name": "vnexpress_rss_tin_moi"},
        "metadata": {"category": "thoi-su"},
    }

    with seeded_db() as db:
        payload = ChatService(db).answer_question(
            "Tóm tắt nhanh mục này",
            mode="summarize_item",
            context_item=context_item,
        )

    assert payload["intent"] == "item_summary"
    assert payload["items"][0]["title"] == "Tin hot tại TP.HCM"
    assert "Tin hot tại TP.HCM" in payload["answer"]


def test_chat_service_handles_freeform_news_title_question(seeded_db) -> None:
    article_title = "Hôm nay 5.4 là Tết Thanh minh 2026, người Việt cần lưu ý gì?"
    with seeded_db() as db:
        db.add(
            Article(
                title=article_title,
                summary=(
                    "Tiết Thanh minh bắt đầu từ hôm nay và có một số điều "
                    "người Việt cần lưu ý."
                ),
                content_clean=(
                    "Tet Thanh minh chinh thuc bat dau vao hom nay. "
                    "Nguoi Viet can luu y cac phong tuc, viec di ta mo va cach giu gin ve sinh."
                ),
                category="doi-song",
                published_at=datetime.now().replace(microsecond=0),
                canonical_url="https://example.com/tet-thanh-minh-2026",
                duplicate_status="unique",
            )
        )
        db.commit()
        payload = ChatService(db).answer_question(article_title)

    assert payload["intent"] == "hot_news"
    assert payload["items"]
    assert payload["items"][0]["title"] == article_title
    assert "Thanh minh" in payload["answer"]
