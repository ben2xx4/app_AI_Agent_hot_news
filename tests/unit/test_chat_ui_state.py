from __future__ import annotations

from app.ui.chat_state import (
    append_chat_message,
    build_chat_meta,
    build_chat_request,
    build_chat_timestamp,
    build_default_chat_messages,
    ensure_pending_user_visible,
    extract_recent_user_questions,
    reset_chat_messages,
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
            "timestamp": messages[0]["timestamp"],
            "intent": None,
            "follow_ups": [],
            "items": [],
        }
    ]
    assert messages[0]["timestamp"]


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


def test_reset_chat_messages_restores_default_assistant_message() -> None:
    messages = [{"role": "user", "content": "Tin hot đâu?", "meta": None}]

    reset_chat_messages(messages)

    assert messages == build_default_chat_messages()


def test_extract_recent_user_questions_returns_distinct_questions() -> None:
    messages = [
        {"role": "assistant", "content": "Xin chào", "meta": None},
        {"role": "user", "content": "Giá vàng hôm nay?", "meta": None},
        {"role": "assistant", "content": "174 triệu", "meta": None},
        {"role": "user", "content": "Thời tiết Hải Phòng thế nào?", "meta": None},
        {"role": "user", "content": "Giá vàng hôm nay?", "meta": None},
    ]

    recent = extract_recent_user_questions(messages, limit=3)

    assert recent == [
        "Giá vàng hôm nay?",
        "Thời tiết Hải Phòng thế nào?",
    ]


def test_build_chat_timestamp_uses_hour_minute_format() -> None:
    timestamp = build_chat_timestamp()

    assert len(timestamp) == 5
    assert ":" in timestamp


def test_build_chat_request_includes_mode_and_context() -> None:
    payload = build_chat_request(
        "Tóm tắt mục này",
        mode="summarize_item",
        context_item={"title": "Tin A", "kind": "news"},
    )

    assert payload["question"] == "Tóm tắt mục này"
    assert payload["mode"] == "summarize_item"
    assert payload["context_item"]["title"] == "Tin A"
