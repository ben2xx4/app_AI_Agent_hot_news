from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class SourceDefinition:
    name: str
    pipeline: str
    source_type: str
    url: str | None = None
    category_default: str | None = None
    active: bool = True
    fetch_interval_minutes: int = 60
    timeout_seconds: int = 15
    retry_count: int = 2
    trust_level: int = 3
    demo_fixture: str | None = None
    parser: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_db_config(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("name", None)
        payload.pop("pipeline", None)
        return payload


@dataclass(slots=True)
class FetchResult:
    text: str
    content_type: str | None
    source_url: str | None
    used_demo: bool = False


@dataclass(slots=True)
class ArticleRecord:
    category: str | None
    title: str
    summary: str | None
    content_clean: str | None
    author: str | None
    published_at: datetime | None
    canonical_url: str
    article_hash: str
    duplicate_status: str
    cluster_key: str


@dataclass(slots=True)
class PriceRecord:
    item_type: str
    item_name: str
    region: str | None
    buy_price: Decimal | None
    sell_price: Decimal | None
    unit: str | None
    effective_at: datetime | None


@dataclass(slots=True)
class WeatherRecord:
    location: str
    forecast_time: datetime | None
    min_temp: Decimal | None
    max_temp: Decimal | None
    humidity: Decimal | None
    wind: str | None
    weather_text: str | None
    warning_text: str | None


@dataclass(slots=True)
class PolicyRecord:
    issuing_agency: str | None
    doc_number: str | None
    title: str
    summary: str | None
    content_clean: str | None
    field: str | None
    issued_at: datetime | None
    effective_at: datetime | None
    canonical_url: str | None


@dataclass(slots=True)
class TrafficRecord:
    event_type: str | None
    title: str
    location: str | None
    start_time: datetime | None
    end_time: datetime | None
    description: str | None
    url: str | None


@dataclass(slots=True)
class PipelineRunSummary:
    pipeline: str
    source_name: str
    total_fetched: int
    total_success: int
    total_failed: int
    status: str
    used_demo: bool = False
    error_message: str | None = None
    total_skipped: int = 0
