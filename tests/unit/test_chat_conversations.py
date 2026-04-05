from __future__ import annotations

from collections.abc import Callable

import pytest

from app.core.text import fold_text
from app.services.chat_service import ChatService


def _assert_hot_news(payload: dict) -> None:
    assert payload["intent"] == "hot_news"
    assert payload["tool_called"] == "get_hot_news"
    assert payload["data"]["items"]
    assert "tin hot" in fold_text(payload["answer"])
    assert "\n- " in payload["answer"]


def _assert_price_lookup(payload: dict) -> None:
    assert payload["intent"] == "price_lookup"
    assert payload["tool_called"] == "get_latest_price"
    assert payload["data"]["items"]
    assert payload["data"]["items"][0]["item_name"] == "ty-gia-usd-ban-ra"
    assert "ty gia usd" in fold_text(payload["answer"])


def _assert_price_compare(payload: dict) -> None:
    assert payload["intent"] == "price_compare"
    assert payload["tool_called"] == "compare_price"
    assert payload["data"]["current"] is not None
    assert payload["data"]["trend"] in {"tăng", "giảm", "không đổi"}
    assert "gia vang" in fold_text(payload["answer"])


def _assert_weather_lookup(payload: dict) -> None:
    assert payload["intent"] == "weather_lookup"
    assert payload["tool_called"] == "get_weather"
    assert payload["data"]["location"] == "Hà Nội"
    assert payload["data"]["weather_text"]
    assert "ha noi" in fold_text(payload["answer"])


def _assert_policy_lookup(payload: dict) -> None:
    assert payload["intent"] == "policy_lookup"
    assert payload["tool_called"] == "search_policy"
    assert payload["data"]["items"]
    assert any(
        "giao duc"
        in " ".join(
            [
                fold_text(item.get("title")),
                fold_text(item.get("summary")),
                fold_text(item.get("field")),
            ]
        )
        for item in payload["data"]["items"]
    )
    assert "van ban" in fold_text(payload["answer"])


def _assert_traffic_lookup(payload: dict) -> None:
    assert payload["intent"] == "traffic_lookup"
    assert payload["tool_called"] == "get_traffic_updates"
    assert payload["data"]["items"]
    assert "giao thong" in fold_text(payload["answer"])


def _assert_topic_summary(payload: dict) -> None:
    assert payload["intent"] == "topic_summary"
    assert payload["tool_called"] == "search_news"
    assert payload["data"]["summary_lines"]
    assert "tom tat nhanh" in fold_text(payload["answer"])


def _assert_source_compare(payload: dict) -> None:
    assert payload["intent"] == "source_compare"
    assert payload["tool_called"] == "search_news"
    assert payload["data"]["comparisons"]
    assert all(item["count"] >= 1 for item in payload["data"]["comparisons"])
    assert "so sanh nguon" in fold_text(payload["answer"])


@pytest.mark.parametrize(
    ("question", "assertion"),
    [
        ("Tin hot hom nay la gi?", _assert_hot_news),
        ("Ty gia USD hom nay la bao nhieu?", _assert_price_lookup),
        ("Gia vang hom nay tang hay giam?", _assert_price_compare),
        ("Ha Noi hom nay co mua khong?", _assert_weather_lookup),
        ("Co chinh sach moi nao ve giao duc khong?", _assert_policy_lookup),
        ("Co tin giao thong nao dang chu y hom nay khong?", _assert_traffic_lookup),
        ("Co nhung chu de nao dang duoc nhieu bao noi toi?", _assert_topic_summary),
        ("Bao nao dang noi nhieu ve giao duc?", _assert_source_compare),
    ],
)
def test_chat_conversation_samples(
    seeded_db,
    question: str,
    assertion: Callable[[dict], None],
) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question(question)

    assertion(payload)
    assert payload["answer"]


def test_chat_conversation_fallback_when_openai_unavailable(monkeypatch, seeded_db) -> None:
    import openai

    class BrokenResponses:
        def create(self, **_: object) -> None:
            raise RuntimeError("OpenAI tam thoi loi")

    class BrokenOpenAI:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.responses = BrokenResponses()

    monkeypatch.setenv("CHAT_USE_OPENAI", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    from app.core.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr(openai, "OpenAI", BrokenOpenAI)

    with seeded_db() as db:
        payload = ChatService(db).answer_question("Bao nao dang noi nhieu ve giao duc?")

    _assert_source_compare(payload)

    get_settings.cache_clear()


def test_chat_unknown_question_does_not_fallback_to_hot_news(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Nhập câu hỏi")

    assert payload["intent"] == "unknown"
    assert payload["tool_called"] == "none"
    assert "chua hieu ro cau hoi" in fold_text(payload["answer"])


def test_chat_politics_question_routes_to_topic_summary(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có gì mới về chính trị?")

    assert payload["intent"] == "topic_summary"
    assert payload["tool_called"] == "search_news"
    assert payload["data"]["topic"] == "chinh tri"
    assert payload["answer"]


def test_chat_finance_question_routes_to_topic_summary(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có tin gì về tài chính hôm nay?")

    assert payload["intent"] == "topic_summary"
    assert payload["tool_called"] == "search_news"
    assert payload["data"]["topic"] == "tai chinh"
    assert payload["answer"]


def test_chat_weather_unknown_location_returns_helpful_message(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Thời tiết Vũng Tàu hôm nay thế nào?")

    assert payload["intent"] == "weather_lookup"
    assert payload["tool_called"] == "get_weather"
    assert "vung tau" in fold_text(payload["answer"])
    assert "ha noi" in fold_text(payload["answer"])
    assert "tp hcm" in fold_text(payload["answer"])


def test_chat_weather_new_city_returns_weather_data(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Thời tiết Hải Phòng hôm nay thế nào?")

    assert payload["intent"] == "weather_lookup"
    assert payload["tool_called"] == "get_weather"
    assert payload["data"]["location"] == "Hải Phòng"
    assert "hai phong" in fold_text(payload["answer"])


def test_chat_weather_warning_query_does_not_parse_fake_location(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có cảnh báo thời tiết nào không?")

    assert payload["intent"] == "weather_lookup"
    assert payload["tool_called"] == "get_weather"
    assert "nao khong" not in fold_text(payload["answer"])
    assert "canh bao thoi tiet" in fold_text(payload["answer"])


def test_chat_blocked_road_question_routes_to_traffic(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có tuyến đường nào đang bị cấm không?")

    assert payload["intent"] == "traffic_lookup"
    assert payload["tool_called"] == "get_traffic_updates"
    assert payload["data"]["focus"] == "blocked_road"
    assert "cam duong" in fold_text(payload["answer"])
    assert payload["answer"]


def test_chat_accident_question_routes_to_traffic_focus(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có tai nạn giao thông nào đáng chú ý không?")

    assert payload["intent"] == "traffic_lookup"
    assert payload["tool_called"] == "get_traffic_updates"
    assert payload["data"]["focus"] == "accident"
    assert payload["answer"]


def test_chat_policy_school_query_finds_education_documents(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Có văn bản nào về học đường không?")

    assert payload["intent"] == "policy_lookup"
    assert payload["tool_called"] == "search_policy"
    assert payload["data"]["items"]
    assert any(
        "giao duc"
        in " ".join(
            [
                fold_text(item.get("title")),
                fold_text(item.get("summary")),
                fold_text(item.get("field")),
            ]
        )
        for item in payload["data"]["items"]
    )
