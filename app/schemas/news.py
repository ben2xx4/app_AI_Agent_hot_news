from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class NewsItem(APIModel):
    id: int
    title: str
    summary: str | None = None
    category: str | None = None
    published_at: datetime | None = None
    canonical_url: str
    duplicate_status: str
    cluster_id: int | None = None
    source: str


class NewsListResponse(APIModel):
    items: list[NewsItem]
    updated_at: datetime | None = None
