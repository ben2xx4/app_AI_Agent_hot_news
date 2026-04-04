from __future__ import annotations

from app.db.session import session_scope
from app.pipelines.common.base import BasePipeline
from app.pipelines.common.records import SourceDefinition, TrafficRecord
from app.pipelines.traffic.parser import parse_traffic_payload
from app.repositories.traffic_repository import TrafficRepository


class TrafficPipeline(BasePipeline[TrafficRecord]):
    pipeline_name = "traffic"

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        super().__init__(demo_only=demo_only, source_names=source_names)
        self.traffic_repo = TrafficRepository()

    def parse(self, source: SourceDefinition, payload: str) -> list[TrafficRecord]:
        return parse_traffic_payload(source, payload)

    def store(self, source_id: int | None, records: list[TrafficRecord]) -> int:
        inserted = 0
        with session_scope() as db:
            for record in records:
                if record.url and self.traffic_repo.get_by_url(db, record.url):
                    continue
                self.traffic_repo.create_event(
                    db,
                    source_id=source_id,
                    event_type=record.event_type,
                    title=record.title,
                    location=record.location,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    description=record.description,
                    url=record.url,
                )
                inserted += 1
        return inserted
