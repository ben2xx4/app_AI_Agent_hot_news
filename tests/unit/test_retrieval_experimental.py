from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import delete, select

from app.core.settings import get_settings
from app.core.text import fold_text
from app.models import DocumentEmbedding
from app.services.chat_service import ChatService
from app.services.policy_service import PolicyService
from app.services.retrieval_index_service import RetrievalIndexService
from app.services.retrieval_service import RetrievalService


@pytest.fixture()
def enable_retrieval(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("EXPERIMENTAL_RETRIEVAL_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_retrieval_index_service_backfills_news_and_policy(enable_retrieval, seeded_db) -> None:
    with seeded_db() as db:
        db.execute(delete(DocumentEmbedding))
        index_service = RetrievalIndexService(db)
        news_stats = index_service.reindex_articles()
        policy_stats = index_service.reindex_policies()
        rows = list(db.scalars(select(DocumentEmbedding)))

    assert news_stats["documents"] >= 1
    assert policy_stats["documents"] >= 1
    assert rows
    assert all(row.embedding_model == "experimental-local-sparse-v1" for row in rows)
    assert all(isinstance(row.embedding_vector_json, dict) for row in rows)


def test_retrieval_service_finds_news_by_semantic_alias(enable_retrieval, seeded_db) -> None:
    with seeded_db() as db:
        hits = RetrievalService(db).search_news_documents("xe cong cong dien", limit=3)

    assert hits
    assert any("buyt dien" in fold_text(hit["chunk_text"]) for hit in hits)


def test_retrieval_service_finds_policy_by_semantic_alias(enable_retrieval, seeded_db) -> None:
    with seeded_db() as db:
        hits = RetrievalService(db).search_policy_documents("hoc duong", limit=3)

    assert hits
    assert any("tuyen sinh" in fold_text(hit["chunk_text"]) for hit in hits)


def test_policy_service_falls_back_to_keyword_when_retrieval_disabled(seeded_db) -> None:
    get_settings.cache_clear()
    with seeded_db() as db:
        payload = PolicyService(db).search_policy(query="giao duc")

    assert payload["items"]
    assert payload["retrieval_used"] is False
    assert payload["match_strategy"] == "keyword"


def test_policy_service_falls_back_when_retrieval_errors(
    enable_retrieval,
    monkeypatch: pytest.MonkeyPatch,
    seeded_db,
) -> None:
    def _raise(*_args, **_kwargs) -> list[dict]:
        raise RuntimeError("retrieval tam thoi loi")

    monkeypatch.setattr(RetrievalService, "search_policy_documents", _raise)

    with seeded_db() as db:
        payload = PolicyService(db).search_policy(query="hoc duong")

    assert payload["items"]
    assert payload["retrieval_used"] is False
    assert payload["match_strategy"] == "keyword"
    assert any(
        "giao duc"
        in " ".join(
            [
                fold_text(item.get("title")),
                fold_text(item.get("summary")),
                fold_text(item.get("field")),
            ]
        )
        for item in payload["items"]
    )


def test_chat_topic_summary_uses_retrieval(enable_retrieval, seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question(
            "Co nhung chu de nao ve xe cong cong dien dang duoc nhieu bao noi toi?"
        )

    assert payload["intent"] == "topic_summary"
    assert payload["data"]["retrieval_used"] is True
    assert any("buyt dien" in fold_text(line) for line in payload["data"]["summary_lines"])


def test_chat_policy_lookup_uses_retrieval(enable_retrieval, seeded_db) -> None:
    with seeded_db() as db:
        payload = ChatService(db).answer_question("Co van ban nao ve hoc duong khong?")

    assert payload["intent"] == "policy_lookup"
    assert payload["data"]["retrieval_used"] is True
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
