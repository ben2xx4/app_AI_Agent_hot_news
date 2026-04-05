from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationItem:
    key: str
    label: str
    icon: str
    description: str


NAVIGATION_ITEMS = (
    NavigationItem(
        key="dashboard",
        label="Tổng quan",
        icon="TQ",
        description="Xem nhanh dữ liệu nổi bật trong ngày và KPI của 5 pipeline.",
    ),
    NavigationItem(
        key="assistant",
        label="Trợ lý AI",
        icon="AI",
        description="Hỏi đáp bằng tiếng Việt, xem lịch sử hội thoại và gợi ý câu hỏi tiếp theo.",
    ),
    NavigationItem(
        key="explorer",
        label="Explorer",
        icon="DX",
        description="Tra cứu dữ liệu chi tiết, lọc, sắp xếp và xuất CSV preview.",
    ),
    NavigationItem(
        key="system",
        label="Hệ thống",
        icon="SYS",
        description="Xem runtime status, scheduler health và attention sources.",
    ),
)

NAVIGATION_BY_KEY = {item.key: item for item in NAVIGATION_ITEMS}
NAVIGATION_BY_LABEL = {item.label: item for item in NAVIGATION_ITEMS}


def navigation_labels() -> list[str]:
    return [item.label for item in NAVIGATION_ITEMS]


def navigation_keys() -> list[str]:
    return [item.key for item in NAVIGATION_ITEMS]


def navigation_label_from_key(key: str) -> str:
    item = NAVIGATION_BY_KEY.get(key)
    if item is None:
        return NAVIGATION_ITEMS[0].label
    return item.label


def navigation_key_from_label(label: str) -> str:
    item = NAVIGATION_BY_LABEL.get(label)
    if item is None:
        return NAVIGATION_ITEMS[0].key
    return item.key


def get_navigation_item(key: str) -> NavigationItem:
    return NAVIGATION_BY_KEY.get(key, NAVIGATION_ITEMS[0])


def build_navigation_state(section_key: str) -> dict[str, str]:
    resolved_key = section_key if section_key in NAVIGATION_BY_KEY else NAVIGATION_ITEMS[0].key
    return {
        "nav_section": resolved_key,
        "nav_section_widget": navigation_label_from_key(resolved_key),
    }
