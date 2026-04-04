from __future__ import annotations

from app.core.settings import get_settings
from app.db.session import session_scope
from app.pipelines.common.base import BasePipeline
from app.pipelines.common.processing import similarity_score, split_into_chunks
from app.pipelines.common.records import ArticleRecord, SourceDefinition
from app.pipelines.news.parser import parse_news_feed
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.news_repository import NewsRepository
from app.services.retrieval_index_service import build_chunk_vectors


class NewsPipeline(BasePipeline[ArticleRecord]):
    pipeline_name = "news"

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        super().__init__(demo_only=demo_only, source_names=source_names)
        self.news_repo = NewsRepository()
        self.embedding_repo = EmbeddingRepository()

    def parse(self, source: SourceDefinition, payload: str) -> list[ArticleRecord]:
        return parse_news_feed(source, payload)

    def store(self, source_id: int | None, records: list[ArticleRecord]) -> int:
        inserted = 0
        with session_scope() as db:
            recent_articles = self.news_repo.get_recent_articles(db, hours=48, limit=500)
            recent_hashes = {article.article_hash for article in recent_articles}

            for record in records:
                if self.news_repo.get_by_canonical_url(db, record.canonical_url):
                    continue
                if record.article_hash in recent_hashes:
                    continue

                duplicate_status = "unique"
                cluster_key = record.cluster_key
                for existing in recent_articles:
                    if similarity_score(record.title, existing.title) >= 0.86:
                        duplicate_status = "near_duplicate"
                        if existing.cluster_id and existing.cluster:
                            cluster_key = existing.cluster.cluster_key
                        break

                cluster = self.news_repo.get_or_create_cluster(
                    db,
                    cluster_key=cluster_key,
                    representative_title=record.title,
                    seen_at=record.published_at,
                )
                created = self.news_repo.create_article(
                    db,
                    source_id=source_id,
                    category=record.category,
                    title=record.title,
                    summary=record.summary,
                    content_clean=record.content_clean,
                    author=record.author,
                    published_at=record.published_at,
                    canonical_url=record.canonical_url,
                    article_hash=record.article_hash,
                    duplicate_status=duplicate_status,
                    cluster_id=cluster.id,
                )
                chunks = split_into_chunks(record.content_clean or record.summary, max_chars=380)
                if chunks:
                    self.embedding_repo.replace_chunks(
                        db,
                        doc_type="article",
                        doc_id=created.id,
                        chunks=chunks,
                        embedding_model=get_settings().experimental_retrieval_model,
                        embedding_vectors=build_chunk_vectors(chunks),
                    )
                inserted += 1
        return inserted
