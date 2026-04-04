from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.schemas.common import APIModel


class PriceSnapshotItem(APIModel):
    id: int
    item_type: str
    item_name: str
    display_name: str
    region: str | None = None
    buy_price: Decimal | None = None
    sell_price: Decimal | None = None
    unit: str | None = None
    display_buy_price: str | None = None
    display_sell_price: str | None = None
    display_unit: str | None = None
    display_value: str | None = None
    effective_at: datetime | None = None
    source: str


class PriceLatestResponse(APIModel):
    items: list[PriceSnapshotItem]
    updated_at: datetime | None = None


class PriceComparison(APIModel):
    item_name: str
    display_name: str | None = None
    current: dict | None = None
    previous: dict | None = None
    delta: Decimal | None = None
    display_delta: str | None = None
    trend: str
    updated_at: datetime | None = None
