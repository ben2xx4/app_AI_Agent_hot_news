from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.text import contains_folded
from app.core.traffic_rules import is_relevant_traffic_content
from app.models import TrafficEvent


class TrafficRepository:
    def create_event(self, db: Session, **payload) -> TrafficEvent:
        event = TrafficEvent(**payload)
        db.add(event)
        db.flush()
        return event

    def get_by_url(self, db: Session, url: str) -> TrafficEvent | None:
        return db.scalar(select(TrafficEvent).where(TrafficEvent.url == url))

    def list_latest(
        self, db: Session, location: str | None = None, limit: int = 10
    ) -> list[TrafficEvent]:
        stmt = select(TrafficEvent)
        stmt = stmt.order_by(desc(TrafficEvent.start_time), desc(TrafficEvent.id)).limit(limit * 3)
        rows = list(db.scalars(stmt))
        rows = [
            row
            for row in rows
            if is_relevant_traffic_content(row.title, row.description, row.location)
        ]
        if location:
            rows = [row for row in rows if contains_folded(row.location, location)]

        deduped: list[TrafficEvent] = []
        seen: set[str] = set()
        for row in rows:
            key = f"{row.title}|{row.location}|{row.start_time}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped[:limit]
