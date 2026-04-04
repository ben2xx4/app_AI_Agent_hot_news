from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.text import expand_news_topic_query, fold_text
from app.models import Article, ArticleCluster


class NewsRepository:
    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    def get_by_canonical_url(self, db: Session, canonical_url: str) -> Article | None:
        return db.scalar(select(Article).where(Article.canonical_url == canonical_url))

    def get_recent_articles(self, db: Session, hours: int = 24, limit: int = 200) -> list[Article]:
        threshold = self._utcnow_naive() - timedelta(hours=hours)
        stmt = (
            select(Article)
            .where(or_(Article.published_at.is_(None), Article.published_at >= threshold))
            .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    def get_by_ids(self, db: Session, ids: list[int]) -> list[Article]:
        if not ids:
            return []
        stmt = select(Article).where(Article.id.in_(ids))
        rows = list(db.scalars(stmt))
        rows_by_id = {row.id: row for row in rows}
        return [rows_by_id[row_id] for row_id in ids if row_id in rows_by_id]

    def get_or_create_cluster(
        self,
        db: Session,
        cluster_key: str,
        representative_title: str,
        seen_at: datetime | None,
    ) -> ArticleCluster:
        cluster = db.scalar(select(ArticleCluster).where(ArticleCluster.cluster_key == cluster_key))
        if cluster:
            cluster.last_seen_at = seen_at or cluster.last_seen_at
            db.add(cluster)
            db.flush()
            return cluster

        cluster = ArticleCluster(
            cluster_key=cluster_key,
            representative_title=representative_title,
            first_seen_at=seen_at,
            last_seen_at=seen_at,
        )
        db.add(cluster)
        db.flush()
        return cluster

    def create_article(self, db: Session, **payload) -> Article:
        article = Article(**payload)
        db.add(article)
        db.flush()
        return article

    def list_hot(self, db: Session, limit: int = 10) -> list[Article]:
        stmt = (
            select(Article)
            .where(Article.duplicate_status != "exact_duplicate")
            .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt))

    def search(self, db: Session, query: str, limit: int = 10) -> list[Article]:
        stmt = (
            select(Article)
            .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
            .limit(max(limit * 10, 100))
        )
        rows = list(db.scalars(stmt))
        queries = expand_news_topic_query(query) or [query]
        strict_topic = fold_text(query) in {"chinh tri", "tai chinh", "kinh te", "giao duc"}
        scored_matches = [
            (
                self._score_search_match(row, queries, strict_topic=strict_topic),
                row,
            )
            for row in rows
        ]
        matches = [
            row
            for score, row in scored_matches
            if score > 0
        ]
        matches.sort(
            key=lambda row: (
                self._score_search_match(row, queries, strict_topic=strict_topic),
                row.published_at or datetime.min,
                row.id,
            ),
            reverse=True,
        )
        return matches[:limit]

    def list_by_cluster(self, db: Session, cluster_id: int) -> list[Article]:
        stmt = (
            select(Article)
            .where(Article.cluster_id == cluster_id)
            .order_by(Article.published_at.desc().nullslast(), Article.id.desc())
        )
        return list(db.scalars(stmt))
    @staticmethod
    def _score_search_match(row: Article, queries: list[str], *, strict_topic: bool) -> int:
        title = fold_text(row.title)
        summary = fold_text(row.summary)
        category = fold_text(row.category)
        content = fold_text(row.content_clean)

        title_summary_score = 0
        content_score = 0
        for candidate in queries:
            if not candidate:
                continue
            if candidate in title:
                title_summary_score += 5
            if candidate in summary:
                title_summary_score += 3
            if candidate in category:
                title_summary_score += 4
            if candidate in content:
                content_score += 1

        if strict_topic and title_summary_score < 4:
            return 0
        return title_summary_score + content_score
