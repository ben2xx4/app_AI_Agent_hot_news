from __future__ import annotations

from app.db.session import session_scope
from app.pipelines.common.base import BasePipeline
from app.pipelines.common.records import SourceDefinition, WeatherRecord
from app.pipelines.weather.parser import parse_weather_payload
from app.repositories.weather_repository import WeatherRepository


class WeatherPipeline(BasePipeline[WeatherRecord]):
    pipeline_name = "weather"

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        super().__init__(demo_only=demo_only, source_names=source_names)
        self.weather_repo = WeatherRepository()

    def parse(self, source: SourceDefinition, payload: str) -> list[WeatherRecord]:
        return parse_weather_payload(source, payload)

    def store(self, source_id: int | None, records: list[WeatherRecord]) -> int:
        inserted = 0
        with session_scope() as db:
            for record in records:
                self.weather_repo.create_snapshot(
                    db,
                    source_id=source_id,
                    location=record.location,
                    forecast_time=record.forecast_time,
                    min_temp=record.min_temp,
                    max_temp=record.max_temp,
                    humidity=record.humidity,
                    wind=record.wind,
                    weather_text=record.weather_text,
                    warning_text=record.warning_text,
                )
                inserted += 1
        return inserted
