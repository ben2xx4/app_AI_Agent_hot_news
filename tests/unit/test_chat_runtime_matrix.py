from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.text import fold_text
from app.services.chat_service import ChatService


@dataclass(frozen=True)
class RuntimeCase:
    question: str
    checker: Callable[[dict], None]


@pytest.fixture(scope="module")
def seeded_matrix_db(tmp_path_factory: pytest.TempPathFactory) -> sessionmaker[Session]:
    db_path = tmp_path_factory.mktemp("chat-matrix") / "matrix.db"
    url = f"sqlite:///{db_path}"

    old_values = {
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
        "SQLITE_FALLBACK_URL": os.environ.get("SQLITE_FALLBACK_URL"),
        "CHAT_USE_OPENAI": os.environ.get("CHAT_USE_OPENAI"),
        "USE_DEMO_ON_FAILURE": os.environ.get("USE_DEMO_ON_FAILURE"),
    }

    os.environ["DATABASE_URL"] = url
    os.environ["SQLITE_FALLBACK_URL"] = url
    os.environ["CHAT_USE_OPENAI"] = "false"
    os.environ["USE_DEMO_ON_FAILURE"] = "true"

    from app.core.settings import get_settings
    from app.db.base import Base
    from app.db.session import get_engine, get_session_factory, set_session_factory_override
    from app.pipelines.news.pipeline import NewsPipeline
    from app.pipelines.policy.pipeline import PolicyPipeline
    from app.pipelines.price.pipeline import PricePipeline
    from app.pipelines.traffic.pipeline import TrafficPipeline
    from app.pipelines.weather.pipeline import WeatherPipeline

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(None)

    import app.models  # noqa: F401

    engine = create_engine(url, future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    set_session_factory_override(session_factory)

    for pipeline_cls in [
        NewsPipeline,
        PricePipeline,
        WeatherPipeline,
        PolicyPipeline,
        TrafficPipeline,
    ]:
        pipeline_cls(demo_only=True).run()

    yield session_factory

    set_session_factory_override(None)
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    engine.dispose()
    for key, value in old_values.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _count_bullets(answer: str) -> int:
    return sum(1 for line in answer.splitlines() if line.startswith("- "))


def _check_hot_basic(payload: dict) -> None:
    assert payload["intent"] == "hot_news"
    assert payload["tool_called"] == "get_hot_news"
    assert payload["data"]["items"]
    assert _count_bullets(payload["answer"]) >= 1


def _check_hot_top_n(limit: int) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "hot_news"
        assert payload["data"]["requested_limit"] == limit
        assert 1 <= _count_bullets(payload["answer"]) <= limit

    return checker


def _check_hot_location(location: str, keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "hot_news"
        assert payload["data"]["requested_location"] == location
        assert payload["data"]["items"]
        titles = " ".join(item["title"] for item in payload["data"]["items"])
        assert keyword in fold_text(titles)
        assert keyword in fold_text(payload["answer"])

    return checker


def _check_hot_topic(topic: str, keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "hot_news"
        assert payload["data"]["requested_query"] == topic
        assert payload["data"]["items"]
        haystack = " ".join(item["title"] for item in payload["data"]["items"])
        assert keyword in fold_text(haystack)

    return checker


def _check_price(item_name: str, keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["data"]
        assert item_name in str(payload["data"]).lower()
        assert keyword in fold_text(payload["answer"])

    return checker


def _check_weather(location: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "weather_lookup"
        assert payload["data"]["location"] == location
        assert fold_text(location) in fold_text(payload["answer"])

    return checker


def _check_policy(keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "policy_lookup"
        assert payload["data"]["items"]
        haystack = " ".join(
            " ".join(
                filter(
                    None,
                    [
                        item.get("title"),
                        item.get("summary"),
                        item.get("field"),
                    ],
                )
            )
            for item in payload["data"]["items"]
        )
        assert keyword in fold_text(haystack)

    return checker


def _check_traffic(keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "traffic_lookup"
        assert keyword in fold_text(payload["answer"])

    return checker


def _check_smalltalk(keyword: str) -> Callable[[dict], None]:
    def checker(payload: dict) -> None:
        assert payload["intent"] == "smalltalk"
        assert keyword in fold_text(payload["answer"])

    return checker


RUNTIME_CASES = [
    RuntimeCase("Tin hot hôm nay là gì?", _check_hot_basic),
    RuntimeCase("Tin hot hom nay la gi?", _check_hot_basic),
    RuntimeCase("Các tin hot hôm nay là gì?", _check_hot_basic),
    RuntimeCase("Top 1 tin hot", _check_hot_top_n(1)),
    RuntimeCase("Top 3 tin hot", _check_hot_top_n(3)),
    RuntimeCase("Top 5 tin hot", _check_hot_top_n(5)),
    RuntimeCase("Top 10 tin hot", _check_hot_top_n(10)),
    RuntimeCase("5 tin hot hôm nay là gì?", _check_hot_top_n(5)),
    RuntimeCase("10 tin hot hôm nay là gì?", _check_hot_top_n(10)),
    RuntimeCase("Ở TP HCM có tin hot gì?", _check_hot_location("TP.HCM", "tp hcm")),
    RuntimeCase("Tin hot ở TP.HCM hôm nay", _check_hot_location("TP.HCM", "tp hcm")),
    RuntimeCase("Ở Hà Nội có tin hot gì?", _check_hot_location("Hà Nội", "ha noi")),
    RuntimeCase("Tin hot ở Hà Nội hôm nay", _check_hot_location("Hà Nội", "ha noi")),
    RuntimeCase("Tin hot về giáo dục hôm nay", _check_hot_topic("giao duc", "giao duc")),
    RuntimeCase("Top 5 tin hot về giáo dục", _check_hot_topic("giao duc", "giao duc")),
    RuntimeCase("Tin hot về tài chính hôm nay", _check_hot_topic("tai chinh", "gia vang")),
    RuntimeCase("Giá vàng hôm nay bao nhiêu?", _check_price("gia-vang-sjc", "gia vang sjc")),
    RuntimeCase(
        "Giá vàng SJC hiện tại là bao nhiêu?",
        _check_price("gia-vang-sjc", "gia vang sjc"),
    ),
    RuntimeCase("Tỷ giá USD hôm nay bao nhiêu?", _check_price("ty-gia-usd-ban-ra", "ty gia usd")),
    RuntimeCase("Giá xăng hôm nay bao nhiêu?", _check_price("gia-xang-ron95-iii", "gia xang")),
    RuntimeCase("Giá vàng hôm nay tăng hay giảm?", _check_price("gia-vang-sjc", "gia vang")),
    RuntimeCase(
        "Tỷ giá USD hôm nay tăng hay giảm?",
        _check_price("ty-gia-usd-ban-ra", "ty gia usd"),
    ),
    RuntimeCase("Thời tiết Hà Nội hôm nay thế nào?", _check_weather("Hà Nội")),
    RuntimeCase("Hà Nội hôm nay có mưa không?", _check_weather("Hà Nội")),
    RuntimeCase("Thời tiết TP HCM hôm nay thế nào?", _check_weather("TP.HCM")),
    RuntimeCase("Thời tiết Hải Phòng hôm nay thế nào?", _check_weather("Hải Phòng")),
    RuntimeCase("Thời tiết Cần Thơ hôm nay thế nào?", _check_weather("Cần Thơ")),
    RuntimeCase("Thời tiết Nha Trang hôm nay thế nào?", _check_weather("Nha Trang")),
    RuntimeCase(
        "Có cảnh báo thời tiết nào không?",
        lambda payload: "canh bao thoi tiet" in fold_text(payload["answer"]),
    ),
    RuntimeCase("Có chính sách mới nào về giáo dục không?", _check_policy("giao duc")),
    RuntimeCase("Có văn bản nào về học đường không?", _check_policy("tuyen sinh")),
    RuntimeCase("Có thông báo mới nào từ Bộ Y tế không?", _check_policy("cap cuu")),
    RuntimeCase("Có tin giao thông nào đáng chú ý hôm nay không?", _check_traffic("giao thong")),
    RuntimeCase("Có tuyến đường nào đang bị cấm không?", _check_traffic("cam duong")),
    RuntimeCase("Có tai nạn giao thông nào đáng chú ý không?", _check_traffic("tai nan")),
    RuntimeCase("Có nơi nào đang ùn tắc không?", _check_traffic("un tac")),
    RuntimeCase("Chào bạn", _check_smalltalk("tro ly hoi dap")),
    RuntimeCase("Bạn là gì?", _check_smalltalk("tro ly ai")),
    RuntimeCase("Bạn giúp được gì?", _check_smalltalk("toi co the ho tro")),
    RuntimeCase("Cảm ơn", _check_smalltalk("khong co gi")),
]


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case, id=f"runtime_{index}")
        for index, case in enumerate(RUNTIME_CASES, start=1)
    ],
)
def test_chat_runtime_matrix(seeded_matrix_db: sessionmaker[Session], case: RuntimeCase) -> None:
    with seeded_matrix_db() as db:
        payload = ChatService(db).answer_question(case.question)

    assert payload["answer"]
    case.checker(payload)
