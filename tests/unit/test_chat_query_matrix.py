from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.agent.intents import IntentRouter


@dataclass(frozen=True)
class RouterCase:
    question: str
    intent: str
    query: str | None = None
    location: str | None = None
    item_name: str | None = None
    focus: str | None = None
    limit: int | None = None


def _build_router_cases() -> list[RouterCase]:
    cases: list[RouterCase] = []

    hot_plain = [
        "Tin hot hôm nay là gì?",
        "Tin hot hom nay la gi?",
        "Tin hot hôm nay có gì?",
        "Các tin hot hôm nay là gì?",
        "Cac tin hot hom nay la gi?",
        "Tin nóng hôm nay là gì?",
        "Tin nong hom nay la gi?",
        "Có tin hot nào hôm nay không?",
        "Co tin hot nao hom nay khong?",
        "Cho tôi tin hot hôm nay",
        "Tin nổi bật hôm nay là gì?",
        "Su kien chinh hom nay la gi?",
        "Hôm nay 5.4 là Tết Thanh minh 2026, người Việt cần lưu ý gì?",
    ]
    cases.extend(
        RouterCase(
            question=question,
            intent="hot_news",
            query=(
                question
                if question == "Hôm nay 5.4 là Tết Thanh minh 2026, người Việt cần lưu ý gì?"
                else None
            ),
        )
        for question in hot_plain
    )

    hot_limit_templates = [
        "Top {n} tin hot",
        "Top {n} tin hot hôm nay",
        "Top {n} tin nóng hôm nay",
        "{n} tin hot hôm nay là gì?",
        "Lấy {n} tin hot hôm nay",
        "Cho tôi top {n} tin hot",
        "Top {n} bài hot hôm nay",
        "{n} tin nóng mới nhất",
    ]
    for limit in (1, 3, 5, 10):
        for template in hot_limit_templates:
            cases.append(
                RouterCase(
                    question=template.format(n=limit),
                    intent="hot_news",
                    limit=limit,
                )
            )

    hot_textual_limits = {
        "top năm tin hot": 5,
        "top mười tin hot hôm nay": 10,
        "năm tin hot hôm nay là gì": 5,
        "mười tin hot hôm nay là gì": 10,
    }
    cases.extend(
        RouterCase(question=question, intent="hot_news", limit=limit)
        for question, limit in hot_textual_limits.items()
    )

    locations = {
        "Hà Nội": ["ở Hà Nội có tin hot gì?", "Tin hot ở Hà Nội hôm nay", "Top 5 tin hot ở Hà Nội"],
        "TP.HCM": ["Ở TP HCM có tin hot gì?", "Tin hot ở TP.HCM hôm nay", "Top 5 tin hot ở TP HCM"],
        "Đà Nẵng": ["Ở Đà Nẵng có tin hot gì?", "Tin hot ở Đà Nẵng hôm nay"],
        "Hải Phòng": ["Ở Hải Phòng có tin hot gì?", "Tin hot ở Hải Phòng hôm nay"],
        "Cần Thơ": ["Ở Cần Thơ có tin hot gì?", "Tin hot ở Cần Thơ hôm nay"],
        "Nha Trang": ["Ở Nha Trang có tin hot gì?", "Tin hot ở Nha Trang hôm nay"],
    }
    for location, questions in locations.items():
        for question in questions:
            limit = 5 if "top 5" in question.lower() else None
            cases.append(
                RouterCase(
                    question=question,
                    intent="hot_news",
                    location=location,
                    limit=limit,
                )
            )

    hot_topics = {
        "giao duc": [
            "Tin hot về giáo dục hôm nay",
            "Top 5 tin hot về giáo dục",
            "Có tin hot nào về giáo dục không?",
            "Top 10 tin nóng về giáo dục",
        ],
        "tai chinh": [
            "Tin hot về tài chính hôm nay",
            "Top 5 tin hot về tài chính",
            "Có tin hot nào về tài chính không?",
            "Top 10 tin nóng về tài chính",
        ],
        "chinh tri": [
            "Tin hot về chính trị hôm nay",
            "Top 5 tin hot về chính trị",
            "Có tin hot nào về chính trị không?",
            "Top 10 tin nóng về chính trị",
        ],
    }
    for topic, questions in hot_topics.items():
        for question in questions:
            limit = None
            if "top 5" in question.lower():
                limit = 5
            elif "top 10" in question.lower():
                limit = 10
            cases.append(
                RouterCase(
                    question=question,
                    intent="hot_news",
                    query=topic,
                    limit=limit,
                )
            )

    combo_cases = [
        ("Top 5 tin hot về giáo dục ở TP HCM", "giao duc", "TP.HCM", 5),
        ("Top 10 tin hot về tài chính ở Hà Nội", "tai chinh", "Hà Nội", 10),
        ("Ở TP HCM có tin hot về giáo dục gì?", "giao duc", "TP.HCM", None),
        ("Ở Hà Nội có tin hot về tài chính gì?", "tai chinh", "Hà Nội", None),
        ("Top 3 tin nóng về chính trị ở Hà Nội", "chinh tri", "Hà Nội", 3),
        ("Top 5 tin nóng về giáo dục ở Hà Nội", "giao duc", "Hà Nội", 5),
    ]
    cases.extend(
        RouterCase(
            question=question,
            intent="hot_news",
            query=query,
            location=location,
            limit=limit,
        )
        for question, query, location, limit in combo_cases
    )

    price_lookup_cases = {
        "Giá vàng hôm nay bao nhiêu?": "gia-vang-sjc",
        "Gia vang hom nay bao nhieu?": "gia-vang-sjc",
        "Giá vàng SJC hiện tại là bao nhiêu?": "gia-vang-sjc",
        "Tỷ giá USD hôm nay bao nhiêu?": "ty-gia-usd-ban-ra",
        "Ty gia USD hom nay bao nhieu?": "ty-gia-usd-ban-ra",
        "USD hôm nay bao nhiêu?": "ty-gia-usd-ban-ra",
        "Giá xăng hôm nay bao nhiêu?": "gia-xang-ron95-iii",
        "Gia xang hom nay bao nhieu?": "gia-xang-ron95-iii",
        "Cho tôi giá xăng hôm nay": "gia-xang-ron95-iii",
    }
    cases.extend(
        RouterCase(question=question, intent="price_lookup", item_name=item_name)
        for question, item_name in price_lookup_cases.items()
    )

    price_compare_cases = {
        "Giá vàng hôm nay tăng hay giảm?": "gia-vang-sjc",
        "Gia vang hom nay tang hay giam?": "gia-vang-sjc",
        "Giá vàng so với hôm qua thế nào?": "gia-vang-sjc",
        "Tỷ giá USD hôm nay tăng hay giảm?": "ty-gia-usd-ban-ra",
        "Tỷ giá USD so với hôm qua thế nào?": "ty-gia-usd-ban-ra",
        "Giá xăng hôm nay tăng hay giảm?": "gia-xang-ron95-iii",
    }
    cases.extend(
        RouterCase(question=question, intent="price_compare", item_name=item_name)
        for question, item_name in price_compare_cases.items()
    )

    weather_cases = [
        ("Thời tiết Hà Nội hôm nay thế nào?", "Hà Nội"),
        ("Thời tiết TP HCM hôm nay thế nào?", "TP.HCM"),
        ("Thời tiết Đà Nẵng hôm nay thế nào?", "Đà Nẵng"),
        ("Thời tiết Hải Phòng hôm nay thế nào?", "Hải Phòng"),
        ("Thời tiết Cần Thơ hôm nay thế nào?", "Cần Thơ"),
        ("Thời tiết Nha Trang hôm nay thế nào?", "Nha Trang"),
        ("Hà Nội hôm nay có mưa không?", "Hà Nội"),
        ("TP HCM hôm nay nóng không?", "TP.HCM"),
        ("Đà Nẵng hôm nay có mưa không?", "Đà Nẵng"),
        ("Có cảnh báo thời tiết nào không?", None),
    ]
    for question, location in weather_cases:
        query = "warning" if "cảnh báo" in question.lower() else None
        cases.append(
            RouterCase(
                question=question,
                intent="weather_lookup",
                location=location,
                query=query,
            )
        )

    policy_cases = [
        ("Có chính sách mới nào về giáo dục không?", "giao duc"),
        ("Co chinh sach moi nao ve giao duc khong?", "giao duc"),
        ("Có văn bản nào về học đường không?", "hoc duong"),
        ("Có thông báo mới nào từ Bộ Y tế không?", "y te"),
        ("Tìm văn bản về giáo dục", "giao duc"),
        ("Tìm văn bản về học đường", "hoc duong"),
        ("Có chính sách nào về y tế không?", "y te"),
        ("Văn bản mới về giáo dục là gì?", "giao duc"),
    ]
    cases.extend(
        RouterCase(question=question, intent="policy_lookup", query=query)
        for question, query in policy_cases
    )

    traffic_cases = [
        ("Có tin giao thông nào đáng chú ý hôm nay không?", None, None),
        ("Có tuyến đường nào đang bị cấm không?", "blocked_road", None),
        ("Có tai nạn giao thông nào đáng chú ý không?", "accident", None),
        ("Có nơi nào đang ùn tắc không?", "congestion", None),
        ("Hà Nội có tuyến đường nào đang bị cấm không?", "blocked_road", "Hà Nội"),
        ("TP HCM có ùn tắc giao thông không?", "congestion", "TP.HCM"),
        ("Có tai nạn giao thông ở Hà Nội không?", "accident", "Hà Nội"),
        ("Giao thông hôm nay thế nào?", None, None),
    ]
    for question, focus, location in traffic_cases:
        cases.append(
            RouterCase(
                question=question,
                intent="traffic_lookup",
                location=location,
                focus=focus,
            )
        )

    topic_summary_cases = [
        ("Có gì mới về chính trị?", "chinh tri"),
        ("Có gì mới về tài chính hôm nay?", "tai chinh"),
        ("Có gì mới về giáo dục?", "giao duc"),
        ("Tóm tắt nhanh về giáo dục", "giao duc"),
        ("Những chủ đề nào đang được nhiều báo nói tới?", None),
        ("Có những chủ đề nào nổi bật hôm nay?", None),
    ]
    cases.extend(
        RouterCase(question=question, intent="topic_summary", query=query)
        for question, query in topic_summary_cases
    )

    source_compare_cases = [
        ("Báo nào đang nói nhiều về giáo dục?", "giao duc"),
        ("Bao nao dang noi nhieu ve giao duc?", "giao duc"),
        ("So sánh nguồn về giáo dục", "giao duc"),
        ("Báo nào đang nói nhiều về tài chính?", "tai chinh"),
        ("So sánh nguồn về tài chính", "tai chinh"),
    ]
    cases.extend(
        RouterCase(question=question, intent="source_compare", query=query)
        for question, query in source_compare_cases
    )

    smalltalk_cases = [
        ("Chào bạn", "smalltalk", "greeting"),
        ("Xin chào", "smalltalk", "greeting"),
        ("Hello", "smalltalk", "greeting"),
        ("Bạn là ai?", "smalltalk", "identity"),
        ("Bạn là gì?", "smalltalk", "identity"),
        ("Bạn giúp được gì?", "smalltalk", "capabilities"),
        ("Bạn có thể làm gì?", "smalltalk", "capabilities"),
        ("Cảm ơn", "smalltalk", "thanks"),
        ("Tạm biệt", "smalltalk", "farewell"),
    ]
    cases.extend(
        RouterCase(question=question, intent=intent, query=query)
        for question, intent, query in smalltalk_cases
    )

    unknown_cases = [
        "Hỏi đáp bằng tiếng Việt",
        "Nhập câu hỏi",
        "abc xyz 123",
        "Gì vậy",
    ]
    cases.extend(
        RouterCase(question=question, intent="unknown", query=question)
        for question in unknown_cases
    )

    return cases


ROUTER_CASES = _build_router_cases()


@pytest.mark.parametrize(
    "case",
    [pytest.param(case, id=f"router_{index}") for index, case in enumerate(ROUTER_CASES, start=1)],
)
def test_router_query_matrix(case: RouterCase) -> None:
    intent = IntentRouter().detect(case.question)

    assert intent.intent == case.intent
    assert intent.query == case.query
    assert intent.location == case.location
    assert intent.item_name == case.item_name
    assert intent.focus == case.focus
    assert intent.limit == case.limit
