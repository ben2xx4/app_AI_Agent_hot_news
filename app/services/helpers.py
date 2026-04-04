from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source


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
    rows = db.execute(
        select(Source.id, Source.source_name, Source.config_json).where(Source.id.in_(clean_ids))
    )
    metadata_map: dict[int, dict[str, object]] = {}
    for row in rows:
        config_json = row.config_json or {}
        metadata_map[row.id] = {
            "source_name": row.source_name,
            "is_demo_only": bool(config_json.get("demo_only_source")),
        }
    return metadata_map
