from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.schemas.common import APIModel


class WeatherResponse(APIModel):
    id: int
    location: str
    forecast_time: datetime | None = None
    min_temp: Decimal | None = None
    max_temp: Decimal | None = None
    humidity: Decimal | None = None
    wind: str | None = None
    weather_text: str | None = None
    warning_text: str | None = None
    source: str
    updated_at: datetime | None = None
