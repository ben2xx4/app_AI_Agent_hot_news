from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.models import (
    Article,
    ArticleCluster,
    CrawlJob,
    DocumentEmbedding,
    RawDocument,
    Source,
    TrafficEvent,
)
from app.services.cleanup_service import CleanupService


def _create_source(db, *, pipeline_name: str, source_name: str) -> Source:
    source = Source(
        pipeline_name=pipeline_name,
        source_name=source_name,
        source_type="json",
        category_default=pipeline_name,
        base_url="https://example.com",
        config_json={},
    )
    db.add(source)
    db.flush()
    return source


def test_cleanup_service_dry_run_keeps_rows_and_files(db_session_factory, tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    old_file = raw_root / "news" / "sample.txt"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("payload cu", encoding="utf-8")

    with db_session_factory() as db:
        news_source = _create_source(db, pipeline_name="news", source_name="vnexpress_rss_tin_moi")
        traffic_source = _create_source(
            db,
            pipeline_name="traffic",
            source_name="vnexpress_traffic_live",
        )
        cluster = ArticleCluster(
            cluster_key="cluster-cu",
            representative_title="Bai cu",
            first_seen_at=datetime(2026, 1, 1, 8, 0, 0),
            last_seen_at=datetime(2026, 1, 1, 8, 0, 0),
        )
        db.add(cluster)
        db.flush()
        article = Article(
            source_id=news_source.id,
            category="tin_tuc",
            title="Bài viết cũ",
            summary="Tóm tắt cũ",
            content_clean="Nội dung cũ",
            author="Test",
            published_at=datetime(2026, 1, 1, 8, 0, 0),
            canonical_url="https://example.com/news-old",
            article_hash="hash-old",
            duplicate_status="unique",
            cluster_id=cluster.id,
        )
        db.add(article)
        db.flush()
        db.add(
            DocumentEmbedding(
                doc_type="article",
                doc_id=article.id,
                chunk_index=0,
                chunk_text="Bài viết cũ",
                embedding_model="experimental-local-sparse-v1",
                embedding_vector_json={"bai": 1.0},
            )
        )
        db.add(
            TrafficEvent(
                source_id=traffic_source.id,
                event_type="phan_luong",
                title="Sự kiện giao thông cũ",
                location="Hà Nội",
                start_time=datetime(2026, 3, 1, 8, 0, 0),
                end_time=None,
                description="Phân luồng giao thông cũ.",
                url="https://example.com/traffic-old",
            )
        )
        db.add(
            RawDocument(
                source_id=news_source.id,
                pipeline_name="news",
                fetch_url="https://example.com/news-old",
                content_type="text/xml",
                raw_path_or_text=str(old_file),
                raw_hash="raw-hash",
                fetch_metadata={"used_demo": False},
                fetched_at=datetime(2026, 3, 1, 8, 0, 0),
            )
        )
        db.add(
            CrawlJob(
                pipeline_name="news",
                source_id=news_source.id,
                status="success",
                started_at=datetime(2026, 3, 1, 8, 0, 0),
                finished_at=datetime(2026, 3, 1, 8, 1, 0),
                total_fetched=1,
                total_success=1,
                total_failed=0,
                created_at=datetime(2026, 3, 1, 8, 1, 0),
            )
        )
        db.commit()

        payload = CleanupService(db, raw_storage_path=raw_root).run(
            apply=False,
            reference_now=datetime(2026, 4, 4, 12, 0, 0),
        )

        assert payload["news"]["matched_rows"] == 1
        assert payload["traffic"]["matched_rows"] == 1
        assert payload["raw_documents"]["matched_rows"] == 1
        assert payload["crawl_jobs"]["matched_rows"] == 1
        assert payload["news"]["deleted_rows"] == 0
        assert payload["raw_documents"]["deleted_files"] == 0
        assert old_file.exists()
        assert db.scalar(select(func.count()).select_from(Article)) == 1


def test_cleanup_service_apply_removes_old_rows_and_files(
    db_session_factory,
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    old_file = raw_root / "traffic" / "old.html"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("du lieu cu", encoding="utf-8")
    new_file = raw_root / "traffic" / "new.html"
    new_file.write_text("du lieu moi", encoding="utf-8")

    with db_session_factory() as db:
        news_source = _create_source(db, pipeline_name="news", source_name="vnexpress_rss_tin_moi")
        traffic_source = _create_source(
            db,
            pipeline_name="traffic",
            source_name="vnexpress_traffic_live",
        )
        cluster = ArticleCluster(
            cluster_key="cluster-cu",
            representative_title="Bai cu",
            first_seen_at=datetime(2026, 1, 1, 8, 0, 0),
            last_seen_at=datetime(2026, 1, 1, 8, 0, 0),
        )
        db.add(cluster)
        db.flush()
        old_article = Article(
            source_id=news_source.id,
            category="tin_tuc",
            title="Bài viết cũ",
            summary="Tóm tắt cũ",
            content_clean="Nội dung cũ",
            author="Test",
            published_at=datetime(2026, 1, 1, 8, 0, 0),
            canonical_url="https://example.com/news-old",
            article_hash="hash-old",
            duplicate_status="unique",
            cluster_id=cluster.id,
        )
        recent_article = Article(
            source_id=news_source.id,
            category="tin_tuc",
            title="Bài viết mới",
            summary="Tóm tắt mới",
            content_clean="Nội dung mới",
            author="Test",
            published_at=datetime(2026, 4, 2, 8, 0, 0),
            canonical_url="https://example.com/news-new",
            article_hash="hash-new",
            duplicate_status="unique",
            cluster_id=None,
        )
        db.add_all([old_article, recent_article])
        db.flush()
        db.add(
            DocumentEmbedding(
                doc_type="article",
                doc_id=old_article.id,
                chunk_index=0,
                chunk_text="Bài viết cũ",
                embedding_model="experimental-local-sparse-v1",
                embedding_vector_json={"bai": 1.0},
            )
        )
        old_traffic = TrafficEvent(
            source_id=traffic_source.id,
            event_type="phan_luong",
            title="Sự kiện giao thông cũ",
            location="Hà Nội",
            start_time=datetime(2026, 3, 1, 8, 0, 0),
            end_time=None,
            description="Phân luồng giao thông cũ.",
            url="https://example.com/traffic-old",
        )
        recent_traffic = TrafficEvent(
            source_id=traffic_source.id,
            event_type="phan_luong",
            title="Sự kiện giao thông mới",
            location="Hà Nội",
            start_time=datetime(2026, 4, 3, 8, 0, 0),
            end_time=None,
            description="Phân luồng giao thông mới.",
            url="https://example.com/traffic-new",
        )
        db.add_all([old_traffic, recent_traffic])
        db.add_all(
            [
                RawDocument(
                    source_id=traffic_source.id,
                    pipeline_name="traffic",
                    fetch_url="https://example.com/traffic-old",
                    content_type="text/html",
                    raw_path_or_text=str(old_file),
                    raw_hash="raw-old",
                    fetch_metadata={"used_demo": False},
                    fetched_at=datetime(2026, 3, 1, 8, 0, 0),
                ),
                RawDocument(
                    source_id=traffic_source.id,
                    pipeline_name="traffic",
                    fetch_url="https://example.com/traffic-new",
                    content_type="text/html",
                    raw_path_or_text=str(new_file),
                    raw_hash="raw-new",
                    fetch_metadata={"used_demo": False},
                    fetched_at=datetime(2026, 4, 3, 8, 0, 0),
                ),
            ]
        )
        db.add_all(
            [
                CrawlJob(
                    pipeline_name="traffic",
                    source_id=traffic_source.id,
                    status="success",
                    started_at=datetime(2026, 3, 1, 8, 0, 0),
                    finished_at=datetime(2026, 3, 1, 8, 1, 0),
                    total_fetched=1,
                    total_success=1,
                    total_failed=0,
                    created_at=datetime(2026, 3, 1, 8, 1, 0),
                ),
                CrawlJob(
                    pipeline_name="traffic",
                    source_id=traffic_source.id,
                    status="success",
                    started_at=datetime(2026, 4, 3, 8, 0, 0),
                    finished_at=datetime(2026, 4, 3, 8, 1, 0),
                    total_fetched=1,
                    total_success=1,
                    total_failed=0,
                    created_at=datetime(2026, 4, 3, 8, 1, 0),
                ),
            ]
        )
        db.commit()

        payload = CleanupService(db, raw_storage_path=raw_root).run(
            apply=True,
            reference_now=datetime(2026, 4, 4, 12, 0, 0),
        )
        db.commit()

        assert payload["news"]["deleted_rows"] == 1
        assert payload["news"]["deleted_related_rows"] == 1
        assert payload["traffic"]["deleted_rows"] == 1
        assert payload["raw_documents"]["deleted_rows"] == 1
        assert payload["raw_documents"]["deleted_files"] == 1
        assert payload["crawl_jobs"]["deleted_rows"] == 1
        assert old_file.exists() is False
        assert new_file.exists() is True

        articles = list(db.scalars(select(Article).order_by(Article.id)))
        traffic_rows = list(db.scalars(select(TrafficEvent).order_by(TrafficEvent.id)))
        raw_rows = list(db.scalars(select(RawDocument).order_by(RawDocument.id)))
        jobs = list(db.scalars(select(CrawlJob).order_by(CrawlJob.id)))
        embeddings = list(db.scalars(select(DocumentEmbedding)))
        clusters = list(db.scalars(select(ArticleCluster)))

    assert [row.title for row in articles] == ["Bài viết mới"]
    assert [row.title for row in traffic_rows] == ["Sự kiện giao thông mới"]
    assert [row.raw_hash for row in raw_rows] == ["raw-new"]
    assert len(jobs) == 1
    assert embeddings == []
    assert clusters == []
