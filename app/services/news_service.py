from __future__ import annotations

from collections import defaultdict
from html import unescape

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.news_hotness import rank_hot_news_rows
from app.core.text import expand_news_search_query, fold_text
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
                "title": unescape(row.title) if row.title else row.title,
                "summary": unescape(row.summary) if row.summary else row.summary,
                "content_clean": (
                    unescape(row.content_clean) if row.content_clean else row.content_clean
                ),
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

    def _matches_hot_news_location(self, row, location: str) -> bool:
        aliases = {
            "Hà Nội": ("ha noi", "hanoi"),
            "TP.HCM": ("tp hcm", "ho chi minh", "sai gon"),
            "Đà Nẵng": ("da nang",),
            "Hải Phòng": ("hai phong",),
            "Cần Thơ": ("can tho",),
            "Nha Trang": ("nha trang",),
        }.get(location, (fold_text(location),))
        haystack = " ".join(
            [
                fold_text(getattr(row, "title", None)),
                fold_text(getattr(row, "summary", None)),
                fold_text(getattr(row, "content_clean", None)),
            ]
        )
        return any(alias and alias in haystack for alias in aliases)

    def _matches_hot_news_query(self, row, query: str) -> bool:
        queries = expand_news_search_query(query) or [fold_text(query)]
        haystack = " ".join(
            [
                fold_text(getattr(row, "title", None)),
                fold_text(getattr(row, "summary", None)),
                fold_text(getattr(row, "content_clean", None)),
                fold_text(getattr(row, "category", None)),
            ]
        )
        return any(candidate and candidate in haystack for candidate in queries)

    def get_hot_news(
        self,
        limit: int = 10,
        *,
        location: str | None = None,
        query: str | None = None,
    ) -> dict:
        candidate_rows = self.repo.get_recent_articles(
            self.db,
            hours=48,
            limit=max(limit * 25, 250),
        )
        filtered_rows = candidate_rows
        if query:
            filtered_rows = [
                row for row in filtered_rows if self._matches_hot_news_query(row, query)
            ]
            if not filtered_rows:
                filtered_rows = self.repo.search(self.db, query=query, limit=max(limit * 4, 20))
        if location:
            filtered_rows = [
                row for row in filtered_rows if self._matches_hot_news_location(row, location)
            ]
        source_map = load_source_name_map(self.db, [row.source_id for row in candidate_rows])
        hot_rows = rank_hot_news_rows(
            filtered_rows,
            source_name_map=source_map,
            limit=limit,
        )
        payload = self._build_payload(hot_rows)
        payload["requested_location"] = location
        payload["requested_query"] = query
        payload["requested_limit"] = limit
        return payload

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
