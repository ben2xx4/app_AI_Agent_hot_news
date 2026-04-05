from __future__ import annotations

from app.ui.experience import (
    QUICK_START_ACTIONS,
    build_sparse_data_notice,
    flatten_chat_suggestions,
    get_follow_up_suggestions,
)


def test_flatten_chat_suggestions_keeps_multiple_domains() -> None:
    prompts = flatten_chat_suggestions()

    assert "Tin hot hôm nay là gì?" in prompts
    assert "Giá vàng SJC hôm nay bao nhiêu?" in prompts
    assert "Có tuyến đường nào đang bị cấm không?" in prompts


def test_sparse_data_notice_warns_when_core_data_is_thin() -> None:
    notice = build_sparse_data_notice(
        [
            {"key": "articles", "title": "Tin tức", "total_rows": 6},
            {"key": "price_snapshots", "title": "Giá cả", "total_rows": 20},
            {"key": "weather_snapshots", "title": "Thời tiết", "total_rows": 2},
            {"key": "policy_documents", "title": "Chính sách", "total_rows": 2},
            {"key": "traffic_events", "title": "Giao thông", "total_rows": 2},
        ]
    )

    assert notice is not None
    assert "scripts/refresh_live_data.py" in notice
    assert "tin tức" in notice.lower()


def test_quick_start_actions_cover_browser_and_chat_entrypoints() -> None:
    assert len(QUICK_START_ACTIONS) == 3
    assert any(action.dataset_title for action in QUICK_START_ACTIONS)
    assert any(action.suggested_question for action in QUICK_START_ACTIONS)


def test_get_follow_up_suggestions_filters_current_question() -> None:
    prompts = get_follow_up_suggestions(
        "price_lookup",
        current_question="Tỷ giá USD hôm nay là bao nhiêu?",
    )

    assert "Tỷ giá USD hôm nay là bao nhiêu?" not in prompts
    assert prompts
