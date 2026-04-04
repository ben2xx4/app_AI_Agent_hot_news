from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source
from app.pipelines.common.records import SourceDefinition


class SourceRepository:
    def get_by_name(self, db: Session, source_name: str) -> Source | None:
        return db.scalar(select(Source).where(Source.source_name == source_name))

    def list_active_by_pipeline(self, db: Session, pipeline_name: str) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.pipeline_name == pipeline_name)
            .where(Source.is_active.is_(True))
            .order_by(Source.source_name.asc())
        )
        return list(db.scalars(stmt))

    def sync_from_definition(self, db: Session, definition: SourceDefinition) -> Source:
        existing = self.get_by_name(db, definition.name)
        payload = {
            "pipeline_name": definition.pipeline,
            "source_type": definition.source_type,
            "category_default": definition.category_default,
            "base_url": definition.url,
            "trust_level": definition.trust_level,
            "is_active": definition.active,
            "fetch_interval_minutes": definition.fetch_interval_minutes,
            "config_json": definition.to_db_config(),
        }

        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            db.add(existing)
            db.flush()
            return existing

        created = Source(source_name=definition.name, **payload)
        db.add(created)
        db.flush()
        return created
