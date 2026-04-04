from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.text import contains_folded, fold_text
from app.models import WeatherSnapshot


class WeatherRepository:
    def create_snapshot(self, db: Session, **payload) -> WeatherSnapshot:
        snapshot = WeatherSnapshot(**payload)
        db.add(snapshot)
        db.flush()
        return snapshot

    def get_latest(self, db: Session, location: str) -> WeatherSnapshot | None:
        stmt = select(WeatherSnapshot).order_by(
            desc(WeatherSnapshot.forecast_time), desc(WeatherSnapshot.id)
        )
        rows = list(db.scalars(stmt.limit(100)))
        exact_fold = fold_text(location)
        for row in rows:
            if fold_text(row.location) == exact_fold:
                return row
        for row in rows:
            if contains_folded(row.location, location):
                return row
        return None

    def list_latest(self, db: Session, limit: int = 10) -> list[WeatherSnapshot]:
        stmt = select(WeatherSnapshot).order_by(
            desc(WeatherSnapshot.forecast_time), desc(WeatherSnapshot.id)
        )
        return list(db.scalars(stmt.limit(limit)))
