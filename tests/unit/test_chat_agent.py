from __future__ import annotations

from app.agent.tool_registry import ToolRegistry
from app.core.settings import get_settings
from app.core.text import fold_text
from app.services.chat_service import ChatService


def test_chat_agent_price_compare(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Gia vang hom nay tang hay giam?")

    assert payload["tool_called"] in {"compare_price", "get_latest_price"}
    assert "gia-vang-sjc" in str(payload["data"]).lower()
    assert payload["answer"]


def test_tool_registry_strict_schema_requires_all_properties(seeded_db) -> None:
    with seeded_db() as db:
        definitions = ToolRegistry(db).definitions()

    for definition in definitions:
        parameters = definition["parameters"]
        assert set(parameters["required"]) == set(parameters["properties"].keys())
        assert parameters["additionalProperties"] is False


def test_chat_agent_fallbacks_when_openai_raises(monkeypatch, seeded_db) -> None:
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
    get_settings.cache_clear()
    monkeypatch.setattr(openai, "OpenAI", BrokenOpenAI)

    with seeded_db() as db:
        payload = ChatService(db).answer_question("Tin hot hom nay la gi?")

    assert payload["tool_called"] == "get_hot_news"
    assert payload["answer"]
    assert payload["data"]["items"]

    get_settings.cache_clear()


def test_chat_agent_returns_guidance_for_ui_label_text(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Hỏi đáp bằng tiếng Việt")

    assert payload["intent"] == "unknown"
    assert payload["tool_called"] == "none"
    assert "chua hieu ro cau hoi" in fold_text(payload["answer"])


def test_chat_agent_handles_basic_greeting(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Chào bạn")

    assert payload["intent"] == "smalltalk"
    assert payload["tool_called"] == "smalltalk"
    assert "tro ly" in fold_text(payload["answer"])


def test_chat_agent_handles_identity_question(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Bạn là gì?")

    assert payload["intent"] == "smalltalk"
    assert payload["tool_called"] == "smalltalk"
    assert "toi la tro ly ai" in fold_text(payload["answer"])


def test_chat_agent_handles_capabilities_question(seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Bạn giúp được gì?")

    assert payload["intent"] == "smalltalk"
    assert payload["tool_called"] == "smalltalk"
    assert "toi co the ho tro" in fold_text(payload["answer"])
    assert "\n- " in payload["answer"]
