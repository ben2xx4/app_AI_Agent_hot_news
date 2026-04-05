from __future__ import annotations

from app.models import Source
from app.services.helpers import load_source_metadata_map


def test_source_metadata_uses_current_config_even_when_db_config_is_stale(
    db_session_factory,
) -> None:
    with db_session_factory() as db:
        source = Source(
            pipeline_name="traffic",
            source_name="vov_traffic_updates",
            source_type="json",
            category_default="giao_thong",
            base_url="https://example.com/demo",
            config_json={},
        )
        db.add(source)
        db.commit()

        metadata_map = load_source_metadata_map(db, [source.id])

    assert metadata_map[source.id]["source_name"] == "vov_traffic_updates"
    assert metadata_map[source.id]["is_demo_only"] is True
