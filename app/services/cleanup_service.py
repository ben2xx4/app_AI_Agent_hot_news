from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.models import (
    Article,
    ArticleCluster,
    CrawlJob,
    DocumentEmbedding,
    RawDocument,
    TrafficEvent,
)
from app.services.retention_config import load_cleanup_retention_policy

logger = get_logger(__name__)


@dataclass(slots=True)
class CleanupBucketSummary:
    cutoff_at: str
    matched_rows: int
    deleted_rows: int
    deleted_related_rows: int = 0
    deleted_files: int = 0
    missing_files: int = 0


class CleanupService:
    def __init__(self, db: Session, *, raw_storage_path: Path | None = None) -> None:
        settings = get_settings()
        self.db = db
        self.raw_storage_path = (raw_storage_path or settings.raw_storage_path).resolve()

    def run(
        self,
        *,
        apply: bool = False,
        news_days: int | None = None,
        traffic_days: int | None = None,
        raw_days: int | None = None,
        crawl_job_days: int | None = None,
        reference_now: datetime | None = None,
    ) -> dict[str, object]:
        current_time = self._normalize_now(reference_now)
        retention = load_cleanup_retention_policy()
        effective_news_days = news_days or retention.articles_days
        effective_traffic_days = traffic_days or retention.traffic_events_days
        effective_raw_days = raw_days or retention.raw_documents_days
        effective_crawl_job_days = crawl_job_days or retention.crawl_jobs_days
        payload = {
            "apply": apply,
            "reference_now": current_time.isoformat(),
            "news": asdict(
                self.cleanup_articles(
                    days=effective_news_days,
                    apply=apply,
                    reference_now=current_time,
                )
            ),
            "traffic": asdict(
                self.cleanup_traffic(
                    days=effective_traffic_days,
                    apply=apply,
                    reference_now=current_time,
                )
            ),
            "raw_documents": asdict(
                self.cleanup_raw_documents(
                    days=effective_raw_days,
                    apply=apply,
                    reference_now=current_time,
                )
            ),
            "crawl_jobs": asdict(
                self.cleanup_crawl_jobs(
                    days=effective_crawl_job_days,
                    apply=apply,
                    reference_now=current_time,
                )
            ),
        }
        if apply:
            self.db.flush()
        return payload

    def cleanup_articles(
        self,
        *,
        days: int,
        apply: bool,
        reference_now: datetime,
    ) -> CleanupBucketSummary:
        cutoff = reference_now - timedelta(days=days)
        rows = list(
            self.db.execute(
                select(Article.id, Article.cluster_id).where(
                    Article.published_at.is_not(None),
                    Article.published_at < cutoff,
                )
            )
        )
        article_ids = [row.id for row in rows]
        deleted_embeddings = 0
        deleted_rows = 0
        if apply and article_ids:
            deleted_embeddings = self.db.execute(
                delete(DocumentEmbedding).where(
                    DocumentEmbedding.doc_type == "article",
                    DocumentEmbedding.doc_id.in_(article_ids),
                )
            ).rowcount or 0
            deleted_rows = self.db.execute(
                delete(Article).where(Article.id.in_(article_ids))
            ).rowcount or 0
            self._delete_orphan_article_clusters()
            logger.info(
                "Cleanup articles: xoa %s bai, %s embedding cu hon %s ngay",
                deleted_rows,
                deleted_embeddings,
                days,
            )
        return CleanupBucketSummary(
            cutoff_at=cutoff.isoformat(),
            matched_rows=len(article_ids),
            deleted_rows=deleted_rows,
            deleted_related_rows=deleted_embeddings,
        )

    def cleanup_traffic(
        self,
        *,
        days: int,
        apply: bool,
        reference_now: datetime,
    ) -> CleanupBucketSummary:
        cutoff = reference_now - timedelta(days=days)
        ids = list(
            self.db.scalars(
                select(TrafficEvent.id).where(
                    TrafficEvent.start_time.is_not(None),
                    TrafficEvent.start_time < cutoff,
                )
            )
        )
        deleted_rows = 0
        if apply and ids:
            deleted_rows = self.db.execute(
                delete(TrafficEvent).where(TrafficEvent.id.in_(ids))
            ).rowcount or 0
            logger.info("Cleanup traffic: xoa %s su kien cu hon %s ngay", deleted_rows, days)
        return CleanupBucketSummary(
            cutoff_at=cutoff.isoformat(),
            matched_rows=len(ids),
            deleted_rows=deleted_rows,
        )

    def cleanup_raw_documents(
        self,
        *,
        days: int,
        apply: bool,
        reference_now: datetime,
    ) -> CleanupBucketSummary:
        cutoff = reference_now - timedelta(days=days)
        rows = list(
            self.db.scalars(
                select(RawDocument).where(
                    RawDocument.fetched_at.is_not(None),
                    RawDocument.fetched_at < cutoff,
                )
            )
        )
        deleted_rows = 0
        deleted_files = 0
        missing_files = 0
        if apply and rows:
            for row in rows:
                file_path = self._resolve_managed_raw_path(row.raw_path_or_text)
                if file_path is None:
                    continue
                if file_path.exists():
                    file_path.unlink()
                    deleted_files += 1
                else:
                    missing_files += 1
            deleted_rows = self.db.execute(
                delete(RawDocument).where(RawDocument.id.in_([row.id for row in rows]))
            ).rowcount or 0
            logger.info(
                "Cleanup raw_documents: xoa %s row, %s file, %s file thieu",
                deleted_rows,
                deleted_files,
                missing_files,
            )
        return CleanupBucketSummary(
            cutoff_at=cutoff.isoformat(),
            matched_rows=len(rows),
            deleted_rows=deleted_rows,
            deleted_files=deleted_files,
            missing_files=missing_files,
        )

    def cleanup_crawl_jobs(
        self,
        *,
        days: int,
        apply: bool,
        reference_now: datetime,
    ) -> CleanupBucketSummary:
        cutoff = reference_now - timedelta(days=days)
        ids = list(
            self.db.scalars(
                select(CrawlJob.id).where(
                    func.coalesce(CrawlJob.finished_at, CrawlJob.created_at) < cutoff
                )
            )
        )
        deleted_rows = 0
        if apply and ids:
            deleted_rows = self.db.execute(
                delete(CrawlJob).where(CrawlJob.id.in_(ids))
            ).rowcount or 0
            logger.info("Cleanup crawl_jobs: xoa %s job cu hon %s ngay", deleted_rows, days)
        return CleanupBucketSummary(
            cutoff_at=cutoff.isoformat(),
            matched_rows=len(ids),
            deleted_rows=deleted_rows,
        )

    def _delete_orphan_article_clusters(self) -> int:
        orphan_ids = list(
            self.db.scalars(
                select(ArticleCluster.id)
                .outerjoin(Article, Article.cluster_id == ArticleCluster.id)
                .group_by(ArticleCluster.id)
                .having(func.count(Article.id) == 0)
            )
        )
        if not orphan_ids:
            return 0
        return self.db.execute(
            delete(ArticleCluster).where(ArticleCluster.id.in_(orphan_ids))
        ).rowcount or 0

    def _resolve_managed_raw_path(self, raw_path_or_text: str | None) -> Path | None:
        if not raw_path_or_text:
            return None
        candidate = Path(raw_path_or_text)
        if not candidate.is_absolute():
            candidate = (self.raw_storage_path / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(self.raw_storage_path)
        except ValueError:
            return None
        return candidate

    def _normalize_now(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(UTC).replace(tzinfo=None)
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)
