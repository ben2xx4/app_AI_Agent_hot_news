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


def test_traffic_service_skips_demo_rows_when_live_rows_exist(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        live_source = Source(
            pipeline_name="traffic",
            source_name="vnexpress_traffic_live",
            source_type="html",
            category_default="giao_thong",
            base_url="https://example.com/live",
            config_json={"max_age_days": 14},
        )
        demo_source = Source(
            pipeline_name="traffic",
            source_name="vov_traffic_updates",
            source_type="json",
            category_default="giao_thong",
            base_url="https://example.com/demo",
            config_json={"demo_only_source": True},
        )
        db.add_all([live_source, demo_source])
        db.flush()

        repo.create_event(
            db,
            source_id=live_source.id,
            event_type="phan_luong",
            title="Tạm cấm đường trên vành đai để thi công",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 8, 0, 0),
            end_time=None,
            description="Phân luồng giao thông theo khung giờ sáng.",
            url="https://example.com/live-event",
        )
        repo.create_event(
            db,
            source_id=demo_source.id,
            event_type="cam_duong_tam_thoi",
            title="Tạm cấm đường một chiều quanh hồ Hoàn Kiếm để tổ chức giải chạy",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 4, 0, 0),
            end_time=None,
            description="Dữ liệu demo giao thông.",
            url="https://example.com/demo-event",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(limit=10)

    assert len(payload["items"]) == 1
    assert payload["items"][0]["source"] == "vnexpress_traffic_live"


def test_traffic_service_filters_out_fuel_policy_roundup(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = Source(
            pipeline_name="traffic",
            source_name="vov_giaothong_traffic_live",
            source_type="html",
            category_default="giao_thong",
            base_url="https://example.com/vov",
            config_json={"max_age_days": 14},
        )
        db.add(source)
        db.flush()

        repo.create_event(
            db,
            source_id=source.id,
            event_type="cap_nhat_giao_thong",
            title="Điều hành giá xăng dầu cần hài hòa lợi ích",
            location="Việt Nam",
            start_time=datetime(2026, 4, 4, 3, 0, 0),
            end_time=None,
            description=(
                "Bài phân tích điều hành giá xăng dầu, có nhắc cao tốc và đường bộ "
                "nhưng không phải cập nhật giao thông hay phân luồng."
            ),
            url="https://example.com/fuel-roundup",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(limit=10)

    assert payload["items"] == []


def test_traffic_service_focus_filters_for_blocked_road(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vnexpress_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="phan_luong",
            title="Tạm cấm đường trên vành đai để thi công hầm chui",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 8, 0, 0),
            end_time=None,
            description="Phân luồng giao thông trong giờ cao điểm.",
            url="https://example.com/blocked-road",
        )
        repo.create_event(
            db,
            source_id=source.id,
            event_type="tai_nan",
            title="Va chạm liên hoàn trên cao tốc, nhiều xe hư hỏng",
            location="Hà Nội",
            start_time=datetime(2026, 4, 4, 9, 0, 0),
            end_time=None,
            description="Cảnh báo tai nạn giao thông trên cao tốc.",
            url="https://example.com/accident",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(focus="blocked_road", limit=10)

    assert len(payload["items"]) == 1
    assert payload["items"][0]["event_type"] == "phan_luong"
    assert "cấm đường" in payload["items"][0]["title"].lower()


def test_traffic_service_blocked_road_focus_ignores_generic_phan_luong_rows(
    db_session_factory,
) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vnexpress_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="phan_luong",
            title="Đề xuất xây cao tốc Bảo Hà - Lai Châu",
            location="Việt Nam",
            start_time=datetime(2026, 4, 4, 8, 0, 0),
            end_time=None,
            description="Thông tin đầu tư hạ tầng giao thông và chuẩn bị dự án cao tốc mới.",
            url="https://example.com/highway-proposal",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(focus="blocked_road", limit=10)

    assert payload["items"] == []


def test_traffic_service_focus_filters_for_accident(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vov_giaothong_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="un_tac",
            title="Kẹt xe kéo dài trên quốc lộ cửa ngõ TP.HCM",
            location="TP.HCM",
            start_time=datetime(2026, 4, 4, 7, 0, 0),
            end_time=None,
            description="Ùn tắc trong khung giờ sáng.",
            url="https://example.com/congestion",
        )
        repo.create_event(
            db,
            source_id=source.id,
            event_type="tai_nan",
            title="Tai nạn giữa xe tải và xe máy trên quốc lộ 1",
            location="TP.HCM",
            start_time=datetime(2026, 4, 4, 8, 0, 0),
            end_time=None,
            description="Tai nạn giao thông khiến một làn xe bị phong tỏa.",
            url="https://example.com/accident",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(focus="accident", limit=10)

    assert len(payload["items"]) == 1
    assert payload["items"][0]["event_type"] == "tai_nan"
    assert "tai nạn" in payload["items"][0]["title"].lower()


def test_traffic_service_accident_focus_ignores_generic_safety_articles(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vov_giaothong_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="tai_nan",
            title="Hầm mới trên cao tốc giúp tài xế đi lại thuận tiện hơn",
            location="Việt Nam",
            start_time=datetime(2026, 4, 4, 8, 0, 0),
            end_time=None,
            description="Bài viết có phần lưu ý an toàn để tránh tai nạn khi đi qua hầm.",
            url="https://example.com/tunnel-safety",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(focus="accident", limit=10)

    assert payload["items"] == []


def test_traffic_service_prioritizes_operational_events_over_generic_policy_rows(
    db_session_factory,
) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_source(db, "vnexpress_traffic_live")
        repo.create_event(
            db,
            source_id=source.id,
            event_type="un_tac",
            title="Bỏ dán tem kiểm định trên kính ôtô từ năm 2027",
            location="Việt Nam",
            start_time=datetime(2026, 4, 4, 8, 25, 0),
            end_time=None,
            description=(
                "Bài về quy định đăng kiểm mới, thay đổi thủ tục và tem kiểm định."
            ),
            url="https://example.com/inspection-policy",
        )
        repo.create_event(
            db,
            source_id=source.id,
            event_type="phan_luong",
            title="Sắp thông xe thêm nhánh cầu tại nút giao lớn nhất TP HCM",
            location="TP.HCM",
            start_time=datetime(2026, 4, 4, 7, 44, 0),
            end_time=None,
            description="Thông xe, phân luồng và giảm ùn tắc khu vực cảng Cát Lái.",
            url="https://example.com/interchange-opening",
        )
        db.commit()

        payload = TrafficService(db).get_traffic_updates(limit=10)

    assert payload["items"][0]["title"].startswith("Sắp thông xe")
    assert all("kiểm định" not in item["title"].lower() for item in payload["items"])
