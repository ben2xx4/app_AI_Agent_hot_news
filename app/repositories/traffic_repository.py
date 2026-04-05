from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.text import contains_folded
from app.core.traffic_rules import (
    is_relevant_traffic_content,
    matches_traffic_focus,
    traffic_relevance_score,
)
from app.models import TrafficEvent
from app.pipelines.common.processing import (
    is_datetime_within_age_window,
    normalize_datetime_for_compare,
)
from app.services.helpers import load_source_metadata_map


class TrafficRepository:
    def create_event(self, db: Session, **payload) -> TrafficEvent:
        event = TrafficEvent(**payload)
        db.add(event)
        db.flush()
        return event

    def get_by_url(self, db: Session, url: str) -> TrafficEvent | None:
        return db.scalar(select(TrafficEvent).where(TrafficEvent.url == url))

    def list_latest(
        self,
        db: Session,
        location: str | None = None,
        focus: str | None = None,
        limit: int = 10,
        reference_now: datetime | None = None,
    ) -> list[TrafficEvent]:
        stmt = select(TrafficEvent)
        stmt = stmt.order_by(desc(TrafficEvent.start_time), desc(TrafficEvent.id)).limit(limit * 3)
        rows = list(db.scalars(stmt))
        source_metadata_map = load_source_metadata_map(db, [row.source_id for row in rows])
        current_time = normalize_datetime_for_compare(reference_now or datetime.now(UTC))
        rows = [
            row
            for row in rows
            if is_relevant_traffic_content(row.title, None, row.description)
            and is_datetime_within_age_window(
                row.start_time,
                source_metadata_map.get(row.source_id or -1, {}).get("max_age_days"),
                now_provider=lambda: current_time,
            )
        ]
        has_live_rows = any(
            not source_metadata_map.get(row.source_id or -1, {}).get("is_demo_only")
            for row in rows
        )
        if has_live_rows:
            rows = [
                row
                for row in rows
                if not source_metadata_map.get(row.source_id or -1, {}).get("is_demo_only")
            ]
        if location:
            rows = [row for row in rows if contains_folded(row.location, location)]

        scored_rows: list[tuple[float, datetime, TrafficEvent]] = []
        for row in rows:
            if focus and not matches_traffic_focus(
                focus, row.event_type, row.title, row.description
            ):
                continue
            score = traffic_relevance_score(
                row.event_type,
                row.title,
                None,
                row.description,
            )
            if score <= 0:
                continue
            sort_time = normalize_datetime_for_compare(row.start_time or current_time)
            scored_rows.append((score, sort_time, row))

        scored_rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
        rows = [row for _, _, row in scored_rows]

        deduped: list[TrafficEvent] = []
        seen: set[str] = set()
        for row in rows:
            key = f"{row.title}|{row.location}|{row.start_time}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped[:limit]
