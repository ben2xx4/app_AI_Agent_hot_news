from __future__ import annotations

from app.ui.navigation import (
    NAVIGATION_ITEMS,
    build_navigation_state,
    get_navigation_item,
    navigation_key_from_label,
    navigation_label_from_key,
    navigation_labels,
)


def test_navigation_labels_cover_four_workspaces() -> None:
    assert len(NAVIGATION_ITEMS) == 4
    assert navigation_labels() == [
        "Tổng quan",
        "Trợ lý AI",
        "Explorer",
        "Hệ thống",
    ]


def test_navigation_round_trip_between_key_and_label() -> None:
    assert navigation_key_from_label("Explorer") == "explorer"
    assert navigation_label_from_key("assistant") == "Trợ lý AI"


def test_get_navigation_item_falls_back_to_dashboard() -> None:
    item = get_navigation_item("khong-ton-tai")

    assert item.key == "dashboard"


def test_build_navigation_state_syncs_widget_label_and_key() -> None:
    payload = build_navigation_state("assistant")

    assert payload == {
        "nav_section": "assistant",
        "nav_section_widget": "Trợ lý AI",
    }
