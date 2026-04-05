from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.text import display_location
from app.repositories.traffic_repository import TrafficRepository
from app.services.helpers import load_source_name_map


class TrafficService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TrafficRepository()

    def get_traffic_updates(
        self,
        location: str | None = None,
        *,
        focus: str | None = None,
        limit: int = 10,
    ) -> dict:
        rows = self.repo.list_latest(self.db, location=location, focus=focus, limit=limit)
        source_map = load_source_name_map(self.db, [row.source_id for row in rows])
        items = [
            {
                "id": row.id,
                "event_type": row.event_type,
                "title": row.title,
                "location": display_location(row.location),
                "start_time": row.start_time,
                "end_time": row.end_time,
                "description": row.description,
                "url": row.url,
                "source": source_map.get(row.source_id or -1, "unknown"),
            }
            for row in rows
        ]
        updated_at = max((row["start_time"] for row in items if row["start_time"]), default=None)
        return {"items": items, "updated_at": updated_at, "focus": focus, "location": location}
