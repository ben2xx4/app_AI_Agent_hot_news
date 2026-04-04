from __future__ import annotations

from app.ui.chat_state import (
    append_chat_message,
    build_chat_meta,
    ensure_pending_user_visible,
)


def test_ensure_pending_user_visible_appends_only_once() -> None:
    messages: list[dict] = []

    ensure_pending_user_visible(messages, "Giá vàng hôm nay là bao nhiêu?")
    ensure_pending_user_visible(messages, "Giá vàng hôm nay là bao nhiêu?")

    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "Giá vàng" in messages[0]["content"]


def test_append_chat_message_keeps_meta() -> None:
    messages: list[dict] = []

    append_chat_message(messages, "assistant", "Đây là câu trả lời", "Intent: hot_news")

    assert messages == [
        {
            "role": "assistant",
            "content": "Đây là câu trả lời",
            "meta": "Intent: hot_news",
        }
    ]


def test_build_chat_meta_contains_sources_and_updated_at() -> None:
    payload = {
        "intent": "price_lookup",
        "tool_called": "get_latest_price",
        "sources": ["sjc_gold_prices_live"],
        "updated_at": "2026-04-04T16:10:00",
    }

    meta = build_chat_meta(payload)

    assert "Intent: price_lookup" in meta
    assert "Tool: get_latest_price" in meta
    assert "Nguồn: sjc_gold_prices_live" in meta
    assert "Cập nhật: 2026-04-04T16:10:00" in meta
