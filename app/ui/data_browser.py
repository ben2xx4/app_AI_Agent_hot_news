from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import session_scope
from app.models import (
    Article,
    CrawlJob,
    DocumentEmbedding,
    PolicyDocument,
    PriceSnapshot,
    RawDocument,
    Source,
    TrafficEvent,
    WeatherSnapshot,
)


@dataclass(frozen=True)
class DatasetDefinition:
    key: str
    title: str
    description: str
    columns: tuple[str, ...]
    search_fields: tuple[str, ...]
    technical: bool = False


DATASET_DEFINITIONS = (
    DatasetDefinition(
        key="articles",
        title="Tin tức",
        description="Bài viết đã ingest và chuẩn hóa từ các nguồn news.",
        columns=(
            "id",
            "title",
            "category",
            "published_at",
            "source_name",
            "duplicate_status",
            "canonical_url",
        ),
        search_fields=("title", "category", "source_name", "canonical_url"),
    ),
    DatasetDefinition(
        key="price_snapshots",
        title="Giá cả",
        description="Giá vàng, xăng dầu và tỷ giá đã lưu trong hệ thống.",
        columns=(
            "id",
            "item_name",
            "item_type",
            "region",
            "buy_price",
            "sell_price",
            "unit",
            "effective_at",
            "source_name",
        ),
        search_fields=("item_name", "item_type", "region", "source_name", "unit"),
    ),
    DatasetDefinition(
        key="weather_snapshots",
        title="Thời tiết",
        description="Bản ghi thời tiết theo địa điểm và thời điểm dự báo.",
        columns=(
            "id",
            "location",
            "weather_text",
            "warning_text",
            "min_temp",
            "max_temp",
            "forecast_time",
            "source_name",
        ),
        search_fields=("location", "weather_text", "warning_text", "source_name"),
    ),
    DatasetDefinition(
        key="policy_documents",
        title="Chính sách",
        description="Văn bản, công báo và thông báo chính sách đã ingest.",
        columns=(
            "id",
            "title",
            "field",
            "issuing_agency",
            "doc_number",
            "issued_at",
            "effective_at",
            "source_name",
            "canonical_url",
        ),
        search_fields=("title", "field", "issuing_agency", "doc_number", "source_name"),
    ),
    DatasetDefinition(
        key="traffic_events",
        title="Giao thông",
        description="Sự kiện giao thông, hạn chế lưu thông và cập nhật tuyến đường.",
        columns=(
            "id",
            "title",
            "event_type",
            "location",
            "start_time",
            "end_time",
            "source_name",
            "url",
        ),
        search_fields=("title", "event_type", "location", "source_name"),
    ),
    DatasetDefinition(
        key="sources",
        title="Nguồn dữ liệu",
        description="Danh sách nguồn đang cấu hình trong hệ thống.",
        columns=(
            "id",
            "source_name",
            "pipeline_name",
            "source_type",
            "is_active",
            "fetch_interval_minutes",
            "base_url",
        ),
        search_fields=("source_name", "pipeline_name", "source_type", "base_url"),
        technical=True,
    ),
    DatasetDefinition(
        key="crawl_jobs",
        title="Lịch sử crawl",
        description="Trạng thái các lần chạy pipeline/source gần đây.",
        columns=(
            "id",
            "pipeline_name",
            "source_name",
            "status",
            "started_at",
            "finished_at",
            "total_fetched",
            "total_success",
            "total_failed",
            "error_message",
        ),
        search_fields=("pipeline_name", "source_name", "status", "error_message"),
        technical=True,
    ),
    DatasetDefinition(
        key="raw_documents",
        title="Raw documents",
        description="Bản ghi raw fetch để debug và đối chiếu nguồn ingest.",
        columns=(
            "id",
            "pipeline_name",
            "source_name",
            "fetch_url",
            "content_type",
            "fetched_at",
        ),
        search_fields=("pipeline_name", "source_name", "fetch_url", "content_type"),
        technical=True,
    ),
    DatasetDefinition(
        key="document_embeddings",
        title="Retrieval index",
        description="Chunk retrieval experimental cho news và policy.",
        columns=(
            "id",
            "doc_type",
            "doc_id",
            "chunk_index",
            "embedding_model",
            "created_at",
        ),
        search_fields=("doc_type", "embedding_model"),
        technical=True,
    ),
)

DATASET_MAP = {dataset.key: dataset for dataset in DATASET_DEFINITIONS}
CORE_DATASET_KEYS = (
    "articles",
    "price_snapshots",
    "weather_snapshots",
    "policy_documents",
    "traffic_events",
)
FILTER_FIELD_LABELS = {
    "pipeline_name": "Pipeline",
    "source_name": "Nguồn",
    "location": "Địa điểm",
    "item_name": "Mặt hàng",
}
DATASET_FILTER_FIELDS = {
    "articles": ("pipeline_name", "source_name"),
    "price_snapshots": ("pipeline_name", "source_name", "item_name"),
    "weather_snapshots": ("pipeline_name", "source_name", "location"),
    "policy_documents": ("pipeline_name", "source_name"),
    "traffic_events": ("pipeline_name", "source_name", "location"),
    "sources": ("pipeline_name", "source_name"),
    "crawl_jobs": ("pipeline_name", "source_name"),
    "raw_documents": ("pipeline_name", "source_name"),
}
DATASET_SORT_FIELDS = {
    "articles": "published_at",
    "price_snapshots": "effective_at",
    "weather_snapshots": "forecast_time",
    "policy_documents": "issued_at",
    "traffic_events": "start_time",
    "sources": "source_name",
    "crawl_jobs": "started_at",
    "raw_documents": "fetched_at",
    "document_embeddings": "created_at",
}


def list_dataset_definitions(
    include_technical: bool = True,
    *,
    technical_only: bool = False,
) -> list[DatasetDefinition]:
    if technical_only:
        return [dataset for dataset in DATASET_DEFINITIONS if dataset.technical]
    if include_technical:
        return list(DATASET_DEFINITIONS)
    return [dataset for dataset in DATASET_DEFINITIONS if not dataset.technical]


def load_dataset_preview(
    dataset_key: str,
    *,
    limit: int = 50,
    keyword: str | None = None,
    structured_filters: dict[str, str] | None = None,
    sort_mode: str = "latest",
    include_technical: bool = True,
    db: Session | None = None,
) -> dict[str, Any]:
    if dataset_key not in DATASET_MAP:
        raise ValueError(f"Khong ho tro dataset: {dataset_key}")

    dataset = DATASET_MAP[dataset_key]
    if dataset.technical and not include_technical:
        raise ValueError(f"Dataset ky thuat dang bi tat: {dataset_key}")

    if db is not None:
        return _build_dataset_payload(
            db,
            dataset,
            limit=limit,
            keyword=keyword,
            structured_filters=structured_filters,
            sort_mode=sort_mode,
        )

    with session_scope() as session:
        return _build_dataset_payload(
            session,
            dataset,
            limit=limit,
            keyword=keyword,
            structured_filters=structured_filters,
            sort_mode=sort_mode,
        )


def load_core_dataset_overview(db: Session | None = None) -> list[dict[str, Any]]:
    if db is not None:
        return _build_core_dataset_overview(db)

    with session_scope() as session:
        return _build_core_dataset_overview(session)


def _build_core_dataset_overview(db: Session) -> list[dict[str, Any]]:
    overview_rows: list[dict[str, Any]] = []
    for dataset_key in CORE_DATASET_KEYS:
        dataset = DATASET_MAP[dataset_key]
        overview_rows.append(
            {
                "key": dataset.key,
                "title": dataset.title,
                "description": dataset.description,
                "total_rows": _count_dataset_rows(db, dataset.key),
            }
        )
    return overview_rows


def _build_dataset_payload(
    db: Session,
    dataset: DatasetDefinition,
    *,
    limit: int,
    keyword: str | None,
    structured_filters: dict[str, str] | None,
    sort_mode: str,
) -> dict[str, Any]:
    rows = _fetch_dataset_rows(db, dataset.key, limit=max(limit * 8, 500))
    total_rows = _count_dataset_rows(db, dataset.key)
    filter_options = _build_filter_options(rows, dataset.key)
    filtered_rows = _apply_structured_filters(rows, structured_filters)
    filtered_rows = _filter_rows(filtered_rows, dataset.search_fields, keyword)
    sorted_rows = _sort_rows(filtered_rows, dataset.key, sort_mode=sort_mode)
    preview_rows = sorted_rows[:limit]
    columns = [
        column for column in dataset.columns if any(column in row for row in preview_rows)
    ] or list(dataset.columns)

    return {
        "dataset_key": dataset.key,
        "title": dataset.title,
        "description": dataset.description,
        "columns": columns,
        "records": preview_rows,
        "total_rows": total_rows,
        "matched_rows": len(sorted_rows),
        "filter_options": filter_options,
        "sort_mode": sort_mode,
    }


def _filter_rows(
    rows: list[dict[str, Any]],
    search_fields: tuple[str, ...],
    keyword: str | None,
) -> list[dict[str, Any]]:
    clean_keyword = (keyword or "").strip().lower()
    if not clean_keyword:
        return rows

    matched_rows: list[dict[str, Any]] = []
    for row in rows:
        haystack = " ".join(_format_cell_for_search(row.get(field)) for field in search_fields)
        if clean_keyword in haystack:
            matched_rows.append(row)
    return matched_rows


def _apply_structured_filters(
    rows: list[dict[str, Any]],
    structured_filters: dict[str, str] | None,
) -> list[dict[str, Any]]:
    if not structured_filters:
        return rows

    filtered_rows = rows
    for field, expected_value in structured_filters.items():
        clean_value = (expected_value or "").strip()
        if not clean_value or clean_value == "Tất cả":
            continue
        filtered_rows = [
            row
            for row in filtered_rows
            if str(row.get(field) or "").strip() == clean_value
        ]
    return filtered_rows


def _build_filter_options(rows: list[dict[str, Any]], dataset_key: str) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for field in DATASET_FILTER_FIELDS.get(dataset_key, ()):
        values = sorted(
            {
                str(row.get(field)).strip()
                for row in rows
                if row.get(field) not in {None, ""}
            }
        )
        if not values:
            continue
        options.append(
            {
                "field": field,
                "label": FILTER_FIELD_LABELS.get(field, field),
                "options": ["Tất cả", *values],
            }
        )
    return options


def _sort_rows(
    rows: list[dict[str, Any]],
    dataset_key: str,
    *,
    sort_mode: str,
) -> list[dict[str, Any]]:
    sort_field = DATASET_SORT_FIELDS.get(dataset_key)
    if not rows:
        return rows
    if sort_field is None:
        return rows

    if sort_mode == "oldest":
        return sorted(
            rows,
            key=lambda row: (str(row.get(sort_field) or ""), int(row.get("id") or 0)),
        )

    return sorted(
        rows,
        key=lambda row: (str(row.get(sort_field) or ""), int(row.get("id") or 0)),
        reverse=True,
    )


def _format_cell_for_search(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, Decimal):
        return format(value, "f").lower()
    return str(value).lower()


def _normalize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_value(value) for key, value in mapping.items()}


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {key: _normalize_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_normalize_value(child) for child in value]
    return value


def _fetch_dataset_rows(db: Session, dataset_key: str, *, limit: int) -> list[dict[str, Any]]:
    if dataset_key == "articles":
        stmt = (
            select(
                Article.id.label("id"),
                Article.title.label("title"),
                Article.summary.label("summary"),
                Article.content_clean.label("content_clean"),
                Article.category.label("category"),
                Article.published_at.label("published_at"),
                Source.source_name.label("source_name"),
                Article.duplicate_status.label("duplicate_status"),
                Article.canonical_url.label("canonical_url"),
            )
            .select_from(Article)
            .join(Source, Source.id == Article.source_id, isouter=True)
            .order_by(Article.published_at.desc(), Article.id.desc())
            .limit(limit)
        )
        rows = [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]
        for row in rows:
            row["pipeline_name"] = "news"
        return rows

    if dataset_key == "price_snapshots":
        stmt = (
            select(
                PriceSnapshot.id.label("id"),
                PriceSnapshot.item_name.label("item_name"),
                PriceSnapshot.item_type.label("item_type"),
                PriceSnapshot.region.label("region"),
                PriceSnapshot.buy_price.label("buy_price"),
                PriceSnapshot.sell_price.label("sell_price"),
                PriceSnapshot.unit.label("unit"),
                PriceSnapshot.effective_at.label("effective_at"),
                Source.source_name.label("source_name"),
            )
            .select_from(PriceSnapshot)
            .join(Source, Source.id == PriceSnapshot.source_id, isouter=True)
            .order_by(PriceSnapshot.effective_at.desc(), PriceSnapshot.id.desc())
            .limit(limit)
        )
        rows = [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]
        for row in rows:
            row["pipeline_name"] = "price"
        return rows

    if dataset_key == "weather_snapshots":
        stmt = (
            select(
                WeatherSnapshot.id.label("id"),
                WeatherSnapshot.location.label("location"),
                WeatherSnapshot.weather_text.label("weather_text"),
                WeatherSnapshot.warning_text.label("warning_text"),
                WeatherSnapshot.min_temp.label("min_temp"),
                WeatherSnapshot.max_temp.label("max_temp"),
                WeatherSnapshot.humidity.label("humidity"),
                WeatherSnapshot.wind.label("wind"),
                WeatherSnapshot.forecast_time.label("forecast_time"),
                Source.source_name.label("source_name"),
            )
            .select_from(WeatherSnapshot)
            .join(Source, Source.id == WeatherSnapshot.source_id, isouter=True)
            .order_by(WeatherSnapshot.forecast_time.desc(), WeatherSnapshot.id.desc())
            .limit(limit)
        )
        rows = [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]
        for row in rows:
            row["pipeline_name"] = "weather"
        return rows

    if dataset_key == "policy_documents":
        stmt = (
            select(
                PolicyDocument.id.label("id"),
                PolicyDocument.title.label("title"),
                PolicyDocument.summary.label("summary"),
                PolicyDocument.content_clean.label("content_clean"),
                PolicyDocument.field.label("field"),
                PolicyDocument.issuing_agency.label("issuing_agency"),
                PolicyDocument.doc_number.label("doc_number"),
                PolicyDocument.issued_at.label("issued_at"),
                PolicyDocument.effective_at.label("effective_at"),
                Source.source_name.label("source_name"),
                PolicyDocument.canonical_url.label("canonical_url"),
            )
            .select_from(PolicyDocument)
            .join(Source, Source.id == PolicyDocument.source_id, isouter=True)
            .order_by(PolicyDocument.issued_at.desc(), PolicyDocument.id.desc())
            .limit(limit)
        )
        rows = [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]
        for row in rows:
            row["pipeline_name"] = "policy"
        return rows

    if dataset_key == "traffic_events":
        stmt = (
            select(
                TrafficEvent.id.label("id"),
                TrafficEvent.title.label("title"),
                TrafficEvent.event_type.label("event_type"),
                TrafficEvent.location.label("location"),
                TrafficEvent.start_time.label("start_time"),
                TrafficEvent.end_time.label("end_time"),
                TrafficEvent.description.label("description"),
                Source.source_name.label("source_name"),
                TrafficEvent.url.label("url"),
            )
            .select_from(TrafficEvent)
            .join(Source, Source.id == TrafficEvent.source_id, isouter=True)
            .order_by(TrafficEvent.start_time.desc(), TrafficEvent.id.desc())
            .limit(limit)
        )
        rows = [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]
        for row in rows:
            row["pipeline_name"] = "traffic"
        return rows

    if dataset_key == "sources":
        stmt = (
            select(
                Source.id.label("id"),
                Source.source_name.label("source_name"),
                Source.pipeline_name.label("pipeline_name"),
                Source.source_type.label("source_type"),
                Source.is_active.label("is_active"),
                Source.fetch_interval_minutes.label("fetch_interval_minutes"),
                Source.base_url.label("base_url"),
            )
            .select_from(Source)
            .order_by(Source.pipeline_name.asc(), Source.source_name.asc())
            .limit(limit)
        )
        return [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]

    if dataset_key == "crawl_jobs":
        stmt = (
            select(
                CrawlJob.id.label("id"),
                CrawlJob.pipeline_name.label("pipeline_name"),
                Source.source_name.label("source_name"),
                CrawlJob.status.label("status"),
                CrawlJob.started_at.label("started_at"),
                CrawlJob.finished_at.label("finished_at"),
                CrawlJob.total_fetched.label("total_fetched"),
                CrawlJob.total_success.label("total_success"),
                CrawlJob.total_failed.label("total_failed"),
                CrawlJob.error_message.label("error_message"),
            )
            .select_from(CrawlJob)
            .join(Source, Source.id == CrawlJob.source_id, isouter=True)
            .order_by(CrawlJob.created_at.desc(), CrawlJob.id.desc())
            .limit(limit)
        )
        return [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]

    if dataset_key == "raw_documents":
        stmt = (
            select(
                RawDocument.id.label("id"),
                RawDocument.pipeline_name.label("pipeline_name"),
                Source.source_name.label("source_name"),
                RawDocument.fetch_url.label("fetch_url"),
                RawDocument.content_type.label("content_type"),
                RawDocument.fetched_at.label("fetched_at"),
            )
            .select_from(RawDocument)
            .join(Source, Source.id == RawDocument.source_id, isouter=True)
            .order_by(RawDocument.fetched_at.desc(), RawDocument.id.desc())
            .limit(limit)
        )
        return [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]

    if dataset_key == "document_embeddings":
        stmt = (
            select(
                DocumentEmbedding.id.label("id"),
                DocumentEmbedding.doc_type.label("doc_type"),
                DocumentEmbedding.doc_id.label("doc_id"),
                DocumentEmbedding.chunk_index.label("chunk_index"),
                DocumentEmbedding.embedding_model.label("embedding_model"),
                DocumentEmbedding.created_at.label("created_at"),
            )
            .select_from(DocumentEmbedding)
            .order_by(DocumentEmbedding.created_at.desc(), DocumentEmbedding.id.desc())
            .limit(limit)
        )
        return [_normalize_mapping(dict(row)) for row in db.execute(stmt).mappings().all()]

    raise ValueError(f"Khong ho tro dataset: {dataset_key}")


def _count_dataset_rows(db: Session, dataset_key: str) -> int:
    model_map = {
        "articles": Article,
        "price_snapshots": PriceSnapshot,
        "weather_snapshots": WeatherSnapshot,
        "policy_documents": PolicyDocument,
        "traffic_events": TrafficEvent,
        "sources": Source,
        "crawl_jobs": CrawlJob,
        "raw_documents": RawDocument,
        "document_embeddings": DocumentEmbedding,
    }
    model = model_map[dataset_key]
    return int(db.scalar(select(func.count()).select_from(model)) or 0)
