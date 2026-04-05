from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatSuggestionGroup:
    label: str
    prompts: tuple[str, ...]


@dataclass(frozen=True)
class QuickStartAction:
    title: str
    description: str
    dataset_title: str | None = None
    suggested_question: str | None = None


CHAT_SUGGESTION_GROUPS = (
    ChatSuggestionGroup(
        label="Tin tức",
        prompts=(
            "Tin hot hôm nay là gì?",
            "Top 5 tin hot hôm nay",
            "Ở TP.HCM có tin hot gì?",
            "Có gì mới về tài chính hôm nay?",
            "Báo nào đang nói nhiều về giáo dục?",
        ),
    ),
    ChatSuggestionGroup(
        label="Giá cả",
        prompts=(
            "Giá vàng SJC hôm nay bao nhiêu?",
            "Tỷ giá USD hôm nay là bao nhiêu?",
            "Giá xăng hôm nay bao nhiêu?",
        ),
    ),
    ChatSuggestionGroup(
        label="Thời tiết và giao thông",
        prompts=(
            "Có cảnh báo thời tiết nào không?",
            "Thời tiết Hải Phòng hôm nay thế nào?",
            "Có tuyến đường nào đang bị cấm không?",
        ),
    ),
    ChatSuggestionGroup(
        label="Chính sách",
        prompts=(
            "Có chính sách mới nào về giáo dục không?",
            "Có văn bản nào về học đường không?",
            "Có thông báo mới nào từ Bộ Y tế không?",
        ),
    ),
)


QUICK_START_ACTIONS = (
    QuickStartAction(
        title="Xem tin mới",
        description=(
            "Nhảy nhanh tới khối dữ liệu tin tức và xem "
            "những bài vừa ingest mà không cần SQL."
        ),
        dataset_title="Tin tức",
    ),
    QuickStartAction(
        title="Hỏi AI",
        description=(
            "Điền sẵn một câu hỏi mẫu và chuyển thẳng sang workspace "
            "Trợ lý AI để bắt đầu nhanh hơn."
        ),
        suggested_question="Tin hot hôm nay là gì?",
    ),
    QuickStartAction(
        title="Mở Explorer",
        description=(
            "Mở thẳng khu Explorer để lọc dữ liệu "
            "theo nhóm nghiệp vụ, nguồn và thời gian."
        ),
        dataset_title="Tin tức",
    ),
)

FOLLOW_UP_SUGGESTIONS = {
    "smalltalk": (
        "Tin hot hôm nay là gì?",
        "Bạn giúp được gì?",
        "Giá vàng SJC hôm nay bao nhiêu?",
    ),
    "hot_news": (
        "Top 5 tin hot hôm nay",
        "Ở TP.HCM có tin hot gì?",
        "Top 10 tin hot về giáo dục",
        "Có gì mới về tài chính hôm nay?",
        "Có chính sách mới nào về giáo dục không?",
        "Có tin giao thông nào đáng chú ý hôm nay không?",
    ),
    "price_lookup": (
        "Giá vàng hôm nay tăng hay giảm?",
        "Tỷ giá USD hôm nay là bao nhiêu?",
        "Giá xăng hôm nay bao nhiêu?",
    ),
    "price_compare": (
        "Giá vàng SJC hôm nay bao nhiêu?",
        "Tỷ giá USD hôm nay là bao nhiêu?",
        "Có gì mới về tài chính hôm nay?",
    ),
    "weather_lookup": (
        "Có cảnh báo thời tiết nào không?",
        "Thời tiết Cần Thơ hôm nay ra sao?",
        "Có tuyến đường nào đang bị cấm không?",
    ),
    "policy_lookup": (
        "Có chính sách mới nào về giáo dục không?",
        "Có văn bản nào về học đường không?",
        "Có thông báo mới nào từ Bộ Y tế không?",
    ),
    "traffic_lookup": (
        "Có tuyến đường nào đang bị cấm không?",
        "Có tai nạn giao thông nào đáng chú ý không?",
        "Có tin giao thông nào đáng chú ý hôm nay không?",
    ),
    "topic_summary": (
        "Có gì mới về tài chính hôm nay?",
        "Có gì mới về chính trị?",
        "Báo nào đang nói nhiều về giáo dục?",
    ),
    "source_compare": (
        "Báo nào đang nói nhiều về giáo dục?",
        "Có gì mới về tài chính hôm nay?",
        "Tin hot hôm nay là gì?",
    ),
    "item_summary": (
        "Tin hot hôm nay là gì?",
        "Có gì mới về tài chính hôm nay?",
        "Có chính sách mới nào về giáo dục không?",
    ),
    "item_context": (
        "Top 5 tin hot hôm nay",
        "Có tuyến đường nào đang bị cấm không?",
        "Thời tiết Hải Phòng hôm nay thế nào?",
    ),
    "unknown": (
        "Tin hot hôm nay là gì?",
        "Giá vàng SJC hôm nay bao nhiêu?",
        "Có cảnh báo thời tiết nào không?",
    ),
}


LOW_DATA_THRESHOLDS = {
    "articles": 50,
    "weather_snapshots": 6,
    "policy_documents": 5,
    "traffic_events": 5,
}


def flatten_chat_suggestions() -> list[str]:
    return [
        prompt
        for group in CHAT_SUGGESTION_GROUPS
        for prompt in group.prompts
    ]


def get_follow_up_suggestions(
    intent: str,
    *,
    current_question: str | None = None,
    limit: int = 3,
) -> list[str]:
    prompts = FOLLOW_UP_SUGGESTIONS.get(intent, FOLLOW_UP_SUGGESTIONS["unknown"])
    normalized_question = (current_question or "").strip().casefold()
    filtered_prompts = [
        prompt
        for prompt in prompts
        if prompt.strip().casefold() != normalized_question
    ]
    return filtered_prompts[:limit]


def build_sparse_data_notice(dataset_overview: list[dict]) -> str | None:
    if not dataset_overview:
        return None

    low_keys: list[str] = []
    for item in dataset_overview:
        threshold = LOW_DATA_THRESHOLDS.get(item["key"])
        if threshold is None:
            continue
        if int(item["total_rows"]) < threshold:
            low_keys.append(item["title"].lower())

    if not low_keys:
        return None

    joined = ", ".join(low_keys)
    return (
        f"Dữ liệu hiện còn mỏng ở các nhóm: {joined}. "
        "Nếu vừa seed demo, hãy chạy scripts/refresh_live_data.py để nạp lại live."
    )
