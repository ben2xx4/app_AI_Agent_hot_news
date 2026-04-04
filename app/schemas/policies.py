from __future__ import annotations

from datetime import datetime

from app.schemas.common import APIModel


class PolicyItem(APIModel):
    id: int
    issuing_agency: str | None = None
    doc_number: str | None = None
    title: str
    summary: str | None = None
    field: str | None = None
    issued_at: datetime | None = None
    effective_at: datetime | None = None
    canonical_url: str | None = None
    source: str


class PolicyListResponse(APIModel):
    items: list[PolicyItem]
    updated_at: datetime | None = None
