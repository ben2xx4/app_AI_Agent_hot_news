from __future__ import annotations

from datetime import datetime

from app.models import Source
from app.pipelines.common.records import SourceDefinition
from app.pipelines.traffic.parser import parse_traffic_payload
from app.repositories.traffic_repository import TrafficRepository


def test_parse_traffic_payload_skips_items_older_than_max_age_days() -> None:
    source = SourceDefinition(
        name="vnexpress_traffic_live",
        pipeline="traffic",
        source_type="html",
        parser="vnexpress_listing_html",
        url="https://vnexpress.net/thoi-su/giao-thong",
        extra={
            "site_root": "https://vnexpress.net",
            "max_items": 3,
            "max_age_days": 14,
        },
    )
    payload = """
    <html>
      <body>
        <article class="item-news">
          <h2 class="title-news">
            <a href="/traffic/old-item">Bài giao thông cũ</a>
          </h2>
        </article>
      </body>
    </html>
    """
    detail_payload = """
    <html>
      <head>
        <meta property="og:title" content="Bài giao thông cũ" />
        <meta property="og:description" content="Cấm đường để phân luồng giao thông." />
        <meta name="pubdate" content="2026-03-01T08:00:00+07:00" />
      </head>
      <body>
        <article class="fck_detail">
          <p class="Normal">Cấm đường quanh nút giao để phân luồng giao thông.</p>
        </article>
      </body>
    </html>
    """

    records = parse_traffic_payload(
        source,
        payload,
        detail_fetcher=lambda _url, _source: detail_payload,
        now_provider=lambda: datetime(2026, 4, 4, 12, 0, 0),
    )

    assert records == []


def _create_traffic_source(db, *, max_age_days: int | None) -> Source:
    config_json = {}
    if max_age_days is not None:
        config_json["max_age_days"] = max_age_days
    source = Source(
        pipeline_name="traffic",
        source_name="vnexpress_traffic_live",
        source_type="html",
        category_default="giao_thong",
        base_url="https://example.com/traffic",
        config_json=config_json,
    )
    db.add(source)
    db.flush()
    return source


def test_traffic_repository_skips_rows_older_than_source_window(db_session_factory) -> None:
    repo = TrafficRepository()
    with db_session_factory() as db:
        source = _create_traffic_source(db, max_age_days=14)
        repo.create_event(
            db,
            source_id=source.id,
            event_type="phan_luong",
            title="Tạm cấm đường để sửa cầu vượt",
            location="Hà Nội",
            start_time=datetime(2026, 4, 2, 8, 0, 0),
            end_time=None,
            description="Phân luồng giao thông tại Hà Nội.",
            url="https://example.com/traffic/recent",
        )
        repo.create_event(
            db,
            source_id=source.id,
            event_type="phan_luong",
            title="Cấm đường từ tháng trước",
            location="Hà Nội",
            start_time=datetime(2026, 3, 10, 8, 0, 0),
            end_time=None,
            description="Bài giao thông cũ đã hết thời gian ưu tiên hiển thị.",
            url="https://example.com/traffic/old",
        )
        db.commit()

        rows = repo.list_latest(db, limit=10, reference_now=datetime(2026, 4, 4, 12, 0, 0))

    assert len(rows) == 1
    assert rows[0].title == "Tạm cấm đường để sửa cầu vượt"
