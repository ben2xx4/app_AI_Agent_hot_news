from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class TrafficItem(APIModel):
    id: int
    event_type: str | None = None
    title: str
    location: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str | None = None
    url: str | None = None
    source: str


class TrafficListResponse(APIModel):
    items: list[TrafficItem]
    updated_at: datetime | None = None
