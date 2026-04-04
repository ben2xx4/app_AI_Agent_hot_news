from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(APIModel):
    status: str
    database_url: str
    database_driver: str


class MessageResponse(APIModel):
    detail: str


class PriceValue(APIModel):
    value: Decimal | None = None
    unit: str | None = None
    updated_at: datetime | None = None
