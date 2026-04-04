from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.text import display_field
from app.repositories.policy_repository import PolicyRepository
from app.services.helpers import load_source_name_map
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)


class PolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PolicyRepository()
        self.retrieval = RetrievalService(db)

    def _build_payload(self, rows: list, retrieval_hits: list[dict] | None = None) -> dict:
        source_map = load_source_name_map(self.db, [row.source_id for row in rows])
        items = [
            {
                "id": row.id,
                "issuing_agency": row.issuing_agency,
                "doc_number": row.doc_number,
                "title": row.title,
                "summary": row.summary,
                "field": display_field(row.field),
                "issued_at": row.issued_at,
                "effective_at": row.effective_at,
                "canonical_url": row.canonical_url,
                "source": source_map.get(row.source_id or -1, "unknown"),
            }
            for row in rows
        ]
        updated_at = max((row["issued_at"] for row in items if row["issued_at"]), default=None)
        return {
            "items": items,
            "updated_at": updated_at,
            "retrieval_used": bool(retrieval_hits),
            "retrieval_mode": "experimental_local_sparse" if retrieval_hits else None,
            "retrieval_hits": retrieval_hits or [],
            "match_strategy": "semantic_fallback" if retrieval_hits else "keyword",
        }

    def _should_try_semantic(
        self,
        *,
        query: str | None,
        field: str | None,
        keyword_rows: list,
        limit: int,
    ) -> bool:
        if not query or field:
            return False
        if not self.retrieval.enabled:
            return False
        return len(keyword_rows) < min(limit, 2)

    def search_policy(
        self, query: str | None = None, field: str | None = None, limit: int = 10
    ) -> dict:
        keyword_rows = self.repo.search(self.db, query=query, field=field, limit=limit)
        retrieval_hits: list[dict] = []

        if self._should_try_semantic(
            query=query,
            field=field,
            keyword_rows=keyword_rows,
            limit=limit,
        ):
            try:
                retrieval_hits = self.retrieval.search_policy_documents(
                    query=query or "",
                    limit=limit,
                )
            except Exception as exc:
                logger.warning("Experimental retrieval policy loi, fallback keyword: %s", exc)
                retrieval_hits = []

        if retrieval_hits:
            semantic_rows = self.repo.get_by_ids(
                self.db, [hit["doc_id"] for hit in retrieval_hits]
            )
            rows = semantic_rows[:]
            seen_ids = {row.id for row in semantic_rows}
            for row in keyword_rows:
                if row.id in seen_ids:
                    continue
                rows.append(row)
                if len(rows) >= limit:
                    break
            return self._build_payload(rows[:limit], retrieval_hits=retrieval_hits)

        return self._build_payload(keyword_rows, retrieval_hits=[])
