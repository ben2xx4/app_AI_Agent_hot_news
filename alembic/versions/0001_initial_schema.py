"""Khoi tao schema dau tien."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pipeline_name", sa.String(length=50), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("category_default", sa.String(length=100), nullable=True),
        sa.Column("base_url", sa.Text(), nullable=True),
        sa.Column("trust_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("config_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_name"),
    )
    op.create_index("ix_sources_pipeline_name", "sources", ["pipeline_name"])
    op.create_index("ix_sources_source_name", "sources", ["source_name"])

    op.create_table(
        "crawl_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pipeline_name", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("total_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_success", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_crawl_jobs_pipeline_name", "crawl_jobs", ["pipeline_name"])
    op.create_index("ix_crawl_jobs_status", "crawl_jobs", ["status"])

    op.create_table(
        "raw_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("pipeline_name", sa.String(length=50), nullable=False),
        sa.Column("fetch_url", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("raw_path_or_text", sa.Text(), nullable=False),
        sa.Column("raw_hash", sa.String(length=128), nullable=False),
        sa.Column("fetch_metadata", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_raw_documents_source_id", "raw_documents", ["source_id"])
    op.create_index("ix_raw_documents_pipeline_name", "raw_documents", ["pipeline_name"])
    op.create_index("ix_raw_documents_raw_hash", "raw_documents", ["raw_hash"])

    op.create_table(
        "article_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(length=255), nullable=False),
        sa.Column("representative_title", sa.Text(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("cluster_key"),
    )
    op.create_index("ix_article_clusters_cluster_key", "article_clusters", ["cluster_key"])

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_clean", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("article_hash", sa.String(length=128), nullable=False),
        sa.Column("duplicate_status", sa.String(length=50), nullable=False, server_default="unique"),
        sa.Column("cluster_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["cluster_id"], ["article_clusters.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.UniqueConstraint("canonical_url"),
    )
    op.create_index("ix_articles_source_id", "articles", ["source_id"])
    op.create_index("ix_articles_category", "articles", ["category"])
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_article_hash", "articles", ["article_hash"])
    op.create_index("ix_articles_source_published", "articles", ["source_id", "published_at"])

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("item_type", sa.String(length=100), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("buy_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("sell_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("effective_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_price_snapshots_source_id", "price_snapshots", ["source_id"])
    op.create_index("ix_price_snapshots_item_type", "price_snapshots", ["item_type"])
    op.create_index("ix_price_snapshots_item_name", "price_snapshots", ["item_name"])
    op.create_index("ix_price_snapshots_region", "price_snapshots", ["region"])
    op.create_index("ix_price_snapshots_effective_at", "price_snapshots", ["effective_at"])
    op.create_index("ix_price_snapshots_lookup", "price_snapshots", ["item_name", "effective_at"])

    op.create_table(
        "weather_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("forecast_time", sa.DateTime(), nullable=True),
        sa.Column("min_temp", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_temp", sa.Numeric(5, 2), nullable=True),
        sa.Column("humidity", sa.Numeric(5, 2), nullable=True),
        sa.Column("wind", sa.String(length=100), nullable=True),
        sa.Column("weather_text", sa.Text(), nullable=True),
        sa.Column("warning_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_weather_snapshots_source_id", "weather_snapshots", ["source_id"])
    op.create_index("ix_weather_snapshots_location", "weather_snapshots", ["location"])
    op.create_index("ix_weather_snapshots_forecast_time", "weather_snapshots", ["forecast_time"])
    op.create_index("ix_weather_snapshots_lookup", "weather_snapshots", ["location", "forecast_time"])

    op.create_table(
        "policy_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("issuing_agency", sa.String(length=255), nullable=True),
        sa.Column("doc_number", sa.String(length=100), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content_clean", sa.Text(), nullable=True),
        sa.Column("field", sa.String(length=100), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        sa.Column("effective_at", sa.DateTime(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_policy_documents_source_id", "policy_documents", ["source_id"])
    op.create_index("ix_policy_documents_issuing_agency", "policy_documents", ["issuing_agency"])
    op.create_index("ix_policy_documents_doc_number", "policy_documents", ["doc_number"])
    op.create_index("ix_policy_documents_field", "policy_documents", ["field"])
    op.create_index("ix_policy_documents_issued_at", "policy_documents", ["issued_at"])
    op.create_index("ix_policy_documents_effective_at", "policy_documents", ["effective_at"])
    op.create_index("ix_policy_documents_lookup", "policy_documents", ["field", "issued_at"])

    op.create_table(
        "traffic_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
    )
    op.create_index("ix_traffic_events_source_id", "traffic_events", ["source_id"])
    op.create_index("ix_traffic_events_event_type", "traffic_events", ["event_type"])
    op.create_index("ix_traffic_events_location", "traffic_events", ["location"])
    op.create_index("ix_traffic_events_start_time", "traffic_events", ["start_time"])
    op.create_index("ix_traffic_events_lookup", "traffic_events", ["location", "start_time"])

    op.create_table(
        "document_embeddings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doc_type", sa.String(length=50), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("embedding_vector_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_document_embeddings_doc_type", "document_embeddings", ["doc_type"])
    op.create_index("ix_document_embeddings_doc_id", "document_embeddings", ["doc_id"])


def downgrade() -> None:
    op.drop_index("ix_document_embeddings_doc_id", table_name="document_embeddings")
    op.drop_index("ix_document_embeddings_doc_type", table_name="document_embeddings")
    op.drop_table("document_embeddings")

    op.drop_index("ix_traffic_events_lookup", table_name="traffic_events")
    op.drop_index("ix_traffic_events_start_time", table_name="traffic_events")
    op.drop_index("ix_traffic_events_location", table_name="traffic_events")
    op.drop_index("ix_traffic_events_event_type", table_name="traffic_events")
    op.drop_index("ix_traffic_events_source_id", table_name="traffic_events")
    op.drop_table("traffic_events")

    op.drop_index("ix_policy_documents_lookup", table_name="policy_documents")
    op.drop_index("ix_policy_documents_effective_at", table_name="policy_documents")
    op.drop_index("ix_policy_documents_issued_at", table_name="policy_documents")
    op.drop_index("ix_policy_documents_field", table_name="policy_documents")
    op.drop_index("ix_policy_documents_doc_number", table_name="policy_documents")
    op.drop_index("ix_policy_documents_issuing_agency", table_name="policy_documents")
    op.drop_index("ix_policy_documents_source_id", table_name="policy_documents")
    op.drop_table("policy_documents")

    op.drop_index("ix_weather_snapshots_lookup", table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_forecast_time", table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_location", table_name="weather_snapshots")
    op.drop_index("ix_weather_snapshots_source_id", table_name="weather_snapshots")
    op.drop_table("weather_snapshots")

    op.drop_index("ix_price_snapshots_lookup", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_effective_at", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_region", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_item_name", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_item_type", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_source_id", table_name="price_snapshots")
    op.drop_table("price_snapshots")

    op.drop_index("ix_articles_source_published", table_name="articles")
    op.drop_index("ix_articles_article_hash", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_index("ix_articles_category", table_name="articles")
    op.drop_index("ix_articles_source_id", table_name="articles")
    op.drop_table("articles")

    op.drop_index("ix_article_clusters_cluster_key", table_name="article_clusters")
    op.drop_table("article_clusters")

    op.drop_index("ix_raw_documents_raw_hash", table_name="raw_documents")
    op.drop_index("ix_raw_documents_pipeline_name", table_name="raw_documents")
    op.drop_index("ix_raw_documents_source_id", table_name="raw_documents")
    op.drop_table("raw_documents")

    op.drop_index("ix_crawl_jobs_status", table_name="crawl_jobs")
    op.drop_index("ix_crawl_jobs_pipeline_name", table_name="crawl_jobs")
    op.drop_table("crawl_jobs")

    op.drop_index("ix_sources_source_name", table_name="sources")
    op.drop_index("ix_sources_pipeline_name", table_name="sources")
    op.drop_table("sources")
