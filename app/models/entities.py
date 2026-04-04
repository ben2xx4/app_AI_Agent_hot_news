from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    pipeline_name = Column(String(50), index=True)
    source_name = Column(String(255), unique=True, index=True)
    source_type = Column(String(50))
    category_default = Column(String(100))
    base_url = Column(Text)
    trust_level = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    fetch_interval_minutes = Column(Integer, default=60)
    config_json = Column(JSON)


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True)
    pipeline_name = Column(String(50), index=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    status = Column(String(50), index=True)
    started_at = Column(DateTime(timezone=False))
    finished_at = Column(DateTime(timezone=False))
    total_fetched = Column(Integer, default=0)
    total_success = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    error_message = Column(Text)
    metadata_json = Column(JSON)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    pipeline_name = Column(String(50), index=True)
    fetch_url = Column(Text)
    content_type = Column(String(100))
    raw_path_or_text = Column(Text)
    raw_hash = Column(String(128), index=True)
    fetch_metadata = Column(JSON)
    fetched_at = Column(DateTime(timezone=False), server_default=func.now())


class ArticleCluster(TimestampMixin, Base):
    __tablename__ = "article_clusters"

    id = Column(Integer, primary_key=True)
    cluster_key = Column(String(255), unique=True, index=True)
    representative_title = Column(Text)
    first_seen_at = Column(DateTime(timezone=False))
    last_seen_at = Column(DateTime(timezone=False))
    articles = relationship("Article", back_populates="cluster")


class Article(TimestampMixin, Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    category = Column(String(100), index=True)
    title = Column(Text)
    summary = Column(Text)
    content_clean = Column(Text)
    author = Column(String(255))
    published_at = Column(DateTime(timezone=False), index=True)
    canonical_url = Column(Text, unique=True)
    article_hash = Column(String(128), index=True)
    duplicate_status = Column(String(50), default="unique")
    cluster_id = Column(Integer, ForeignKey("article_clusters.id"))
    cluster = relationship("ArticleCluster", back_populates="articles")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    item_type = Column(String(100), index=True)
    item_name = Column(String(255), index=True)
    region = Column(String(100), index=True)
    buy_price = Column(Numeric(18, 2))
    sell_price = Column(Numeric(18, 2))
    unit = Column(String(50))
    effective_at = Column(DateTime(timezone=False), index=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    location = Column(String(255), index=True)
    forecast_time = Column(DateTime(timezone=False), index=True)
    min_temp = Column(Numeric(5, 2))
    max_temp = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    wind = Column(String(100))
    weather_text = Column(Text)
    warning_text = Column(Text)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


class PolicyDocument(TimestampMixin, Base):
    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    issuing_agency = Column(String(255), index=True)
    doc_number = Column(String(100), index=True)
    title = Column(Text)
    summary = Column(Text)
    content_clean = Column(Text)
    field = Column(String(100), index=True)
    issued_at = Column(DateTime(timezone=False), index=True)
    effective_at = Column(DateTime(timezone=False), index=True)
    canonical_url = Column(Text)


class TrafficEvent(TimestampMixin, Base):
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), index=True)
    event_type = Column(String(100), index=True)
    title = Column(Text)
    location = Column(String(255), index=True)
    start_time = Column(DateTime(timezone=False), index=True)
    end_time = Column(DateTime(timezone=False))
    description = Column(Text)
    url = Column(Text)


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True)
    doc_type = Column(String(50), index=True)
    doc_id = Column(Integer, index=True)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text)
    embedding_model = Column(String(100))
    embedding_vector_json = Column(JSON)
    created_at = Column(DateTime(timezone=False), server_default=func.now())


Index("ix_articles_source_published", Article.source_id, Article.published_at)
Index("ix_price_snapshots_lookup", PriceSnapshot.item_name, PriceSnapshot.effective_at)
Index("ix_weather_snapshots_lookup", WeatherSnapshot.location, WeatherSnapshot.forecast_time)
Index("ix_policy_documents_lookup", PolicyDocument.field, PolicyDocument.issued_at)
Index("ix_traffic_events_lookup", TrafficEvent.location, TrafficEvent.start_time)
