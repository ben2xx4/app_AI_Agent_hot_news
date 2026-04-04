from __future__ import annotations

from datetime import datetime

from app.models import Source
from app.repositories.traffic_repository import TrafficRepository
from app.services.traffic_service import TrafficService


def _create_source(db, source_name: str) -> Source:
    source = Source(
        pipeline_name="traffic",
        source_name=source_name,
        source_type="html",
        category_default="giao_thong",
        base_url="https://example.com",
        config_json={},
    )
    db.add(source)
    db.flush()
    return source


def test_traffic_service_filters_out_non_traffic_rows(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vov_giaothong_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="cap_nhat_giao_thong",
            title="Tạm cấm đường quanh hồ Hoàn Kiếm để tổ chức giải chạy",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 4, 0, 0),
            end_time=None,
            description="Phân luồng giao thông và cấm đường theo khung giờ.",
            url="https://example.com/traffic",
        )
        repo.create_event(
            db,
            source_id=source.id,
            event_type="cap_nhat_giao_thong",
            title="Hà Nội đẩy mạnh công tác tuyên truyền về an toàn thực phẩm",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 5, 0, 0),
            end_time=None,
            description="Bài viết về an toàn thực phẩm, không phải giao thông.",
            url="https://example.com/non-traffic",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(limit=10)

    assert len(payload["items"]) == 1
    assert "cấm đường" in payload["items"][0]["title"].lower()
