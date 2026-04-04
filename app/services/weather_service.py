from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.text import display_location
from app.repositories.weather_repository import WeatherRepository
from app.services.helpers import load_source_name_map


class WeatherService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WeatherRepository()

    def get_weather(self, location: str) -> dict | None:
        row = self.repo.get_latest(self.db, location=location)
        if not row:
            return None
        source_map = load_source_name_map(self.db, [row.source_id])
        return {
            "id": row.id,
            "location": display_location(row.location),
            "forecast_time": row.forecast_time,
            "min_temp": row.min_temp,
            "max_temp": row.max_temp,
            "humidity": row.humidity,
            "wind": row.wind,
            "weather_text": row.weather_text,
            "warning_text": row.warning_text,
            "source": source_map.get(row.source_id or -1, "unknown"),
            "updated_at": row.forecast_time,
        }

    def list_available_locations(self) -> list[str]:
        rows = self.repo.list_latest(self.db, limit=20)
        seen: set[str] = set()
        locations: list[str] = []
        for row in rows:
            label = display_location(row.location) or row.location
            if not label or label in seen:
                continue
            seen.add(label)
            locations.append(label)
        return locations

    def get_warning_summary(self) -> dict:
        rows = self.repo.list_latest(self.db, limit=20)
        source_map = load_source_name_map(self.db, [row.source_id for row in rows])
        warning_items = [
            {
                "location": display_location(row.location),
                "warning_text": row.warning_text,
                "forecast_time": row.forecast_time,
                "source": source_map.get(row.source_id or -1, "unknown"),
            }
            for row in rows
            if row.warning_text
        ]
        updated_at = max(
            (item["forecast_time"] for item in warning_items if item["forecast_time"]),
            default=max((row.forecast_time for row in rows if row.forecast_time), default=None),
        )
        return {
            "warning_query": True,
            "items": warning_items,
            "available_locations": self.list_available_locations(),
            "updated_at": updated_at,
        }
