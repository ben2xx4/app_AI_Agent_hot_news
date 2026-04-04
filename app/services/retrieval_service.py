from __future__ import annotations

from math import sqrt
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.models import DocumentEmbedding
from app.services.retrieval_index_service import build_sparse_vector

logger = get_logger(__name__)


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.experimental_retrieval_enabled

    def search_news_documents(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        return self._search_documents(query=query, doc_type="article", limit=limit)

    def search_policy_documents(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        return self._search_documents(query=query, doc_type="policy", limit=limit)

    def _search_documents(
        self,
        *,
        query: str,
        doc_type: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not self.enabled:
            logger.debug("Experimental retrieval dang tat, bo qua truy van doc_type=%s", doc_type)
            return []

        query_vector = build_sparse_vector(query)
        if not query_vector:
            return []

        stmt = (
            select(DocumentEmbedding)
            .where(DocumentEmbedding.doc_type == doc_type)
            .where(DocumentEmbedding.embedding_vector_json.is_not(None))
        )
        rows = list(self.db.scalars(stmt))
        if not rows:
            logger.info("Chua co retrieval index cho doc_type=%s", doc_type)
            return []

        hits_by_doc: dict[int, dict[str, Any]] = {}
        min_score = self.settings.experimental_retrieval_min_score
        for row in rows:
            vector = self._coerce_sparse_vector(row.embedding_vector_json)
            if not vector:
                continue
            if (
                row.embedding_model
                and row.embedding_model != self.settings.experimental_retrieval_model
            ):
                continue

            score = self._cosine_score(query_vector, vector)
            if score < min_score:
                continue

            hit = hits_by_doc.get(row.doc_id)
            if hit is None or score > hit["score"]:
                hits_by_doc[row.doc_id] = {
                    "doc_id": row.doc_id,
                    "doc_type": row.doc_type,
                    "score": round(score, 4),
                    "chunk_index": row.chunk_index,
                    "chunk_text": row.chunk_text,
                }

        ordered_hits = sorted(hits_by_doc.values(), key=lambda item: item["score"], reverse=True)
        limited_hits = ordered_hits[: limit or self.settings.experimental_retrieval_limit]
        if limited_hits:
            logger.info(
                "Experimental retrieval tra ve %s ket qua cho doc_type=%s, query=%s",
                len(limited_hits),
                doc_type,
                query,
            )
        return limited_hits

    def _coerce_sparse_vector(self, value: Any) -> dict[str, float]:
        if not isinstance(value, dict):
            return {}
        normalized: dict[str, float] = {}
        for key, raw_score in value.items():
            if not isinstance(key, str):
                continue
            try:
                normalized[key] = float(raw_score)
            except (TypeError, ValueError):
                continue
        return normalized

    def _cosine_score(
        self,
        query_vector: dict[str, float],
        candidate_vector: dict[str, float],
    ) -> float:
        if not query_vector or not candidate_vector:
            return 0.0
        dot_product = sum(
            score * candidate_vector.get(feature, 0.0)
            for feature, score in query_vector.items()
        )
        candidate_norm = sqrt(sum(score * score for score in candidate_vector.values()))
        if candidate_norm <= 0:
            return 0.0
        return dot_product / candidate_norm
