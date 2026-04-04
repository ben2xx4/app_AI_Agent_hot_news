from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.repositories.news_repository import NewsRepository
from app.services.helpers import load_source_name_map
from app.services.retrieval_service import RetrievalService

logger = get_logger(__name__)


class NewsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NewsRepository()
        self.retrieval = RetrievalService(db)

    def _build_payload(self, rows: list) -> dict:
        source_map = load_source_name_map(self.db, [row.source_id for row in rows])
        items = [
            {
                "id": row.id,
                "title": row.title,
                "summary": row.summary,
                "content_clean": row.content_clean,
                "category": row.category,
                "published_at": row.published_at,
                "canonical_url": row.canonical_url,
                "duplicate_status": row.duplicate_status,
                "cluster_id": row.cluster_id,
                "source": source_map.get(row.source_id or -1, "unknown"),
            }
            for row in rows
        ]
        updated_at = max(
            (row["published_at"] for row in items if row["published_at"]), default=None
        )
        return {"items": items, "updated_at": updated_at}

    def get_hot_news(self, limit: int = 10) -> dict:
        return self._build_payload(self.repo.list_hot(self.db, limit=limit))

    def search_news(self, query: str, limit: int = 10) -> dict:
        return self._build_payload(self.repo.search(self.db, query=query, limit=limit))

    def summarize_topic(self, query: str | None = None, limit: int = 5) -> dict:
        retrieval_hits: list[dict] = []
        payload: dict | None = None

        if query:
            try:
                retrieval_hits = self.retrieval.search_news_documents(query=query, limit=limit)
            except Exception as exc:
                logger.warning("Experimental retrieval news loi, fallback keyword: %s", exc)
                retrieval_hits = []

        if retrieval_hits:
            rows = self.repo.get_by_ids(self.db, [hit["doc_id"] for hit in retrieval_hits])
            payload = self._build_payload(rows)

        if payload is None:
            payload = (
                self.get_hot_news(limit=limit)
                if not query
                else self.search_news(query=query, limit=limit)
            )

        items = payload["items"]
        cluster_count = len({item["cluster_id"] for item in items if item["cluster_id"]})
        titles = [item["title"] for item in items]
        return {
            "topic": query or "tin hot hom nay",
            "items": items,
            "summary_lines": titles,
            "cluster_count": cluster_count,
            "updated_at": payload["updated_at"],
            "sources": sorted({item["source"] for item in items}),
            "retrieval_used": bool(retrieval_hits),
            "retrieval_mode": "experimental_local_sparse" if retrieval_hits else None,
            "retrieval_hits": retrieval_hits,
        }

    def compare_sources(self, query: str | None = None, limit: int = 10) -> dict:
        payload = (
            self.get_hot_news(limit=limit)
            if not query
            else self.search_news(query=query, limit=limit)
        )
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in payload["items"]:
            grouped[item["source"]].append(item["title"])
        comparisons = [
            {"source": source, "titles": titles[:3], "count": len(titles)}
            for source, titles in grouped.items()
        ]
        return {
            "query": query or "tin hot hom nay",
            "comparisons": comparisons,
            "updated_at": payload["updated_at"],
        }
