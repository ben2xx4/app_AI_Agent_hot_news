from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source
from app.pipelines.common.source_loader import load_source_definitions


def _load_current_source_config_map() -> dict[str, dict[str, object]]:
    return {
        source.name: dict(source.extra)
        for source in load_source_definitions()
    }


def load_source_name_map(db: Session, source_ids: Iterable[int | None]) -> dict[int, str]:
    metadata_map = load_source_metadata_map(db, source_ids)
    return {
        source_id: metadata["source_name"]
        for source_id, metadata in metadata_map.items()
    }


def load_source_metadata_map(
    db: Session,
    source_ids: Iterable[int | None],
) -> dict[int, dict[str, object]]:
    clean_ids = {source_id for source_id in source_ids if source_id is not None}
    if not clean_ids:
        return {}
    current_config_map = _load_current_source_config_map()
    rows = db.execute(
        select(Source.id, Source.source_name, Source.config_json).where(Source.id.in_(clean_ids))
    )
    metadata_map: dict[int, dict[str, object]] = {}
    for row in rows:
        config_json = row.config_json or {}
        current_config = current_config_map.get(row.source_name, {})
        effective_config = {**config_json, **current_config}
        metadata_map[row.id] = {
            "source_name": row.source_name,
            "is_demo_only": bool(effective_config.get("demo_only_source")),
            "max_age_days": effective_config.get("max_age_days"),
        }
    return metadata_map
