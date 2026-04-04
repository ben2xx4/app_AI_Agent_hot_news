from __future__ import annotations

from pathlib import Path

from app.pipelines.common.records import SourceDefinition
from app.pipelines.news.parser import parse_news_feed


def test_parse_news_feed_fixture() -> None:
    source = SourceDefinition(
        name="vnexpress_rss_tin_moi",
        pipeline="news",
        source_type="rss",
        category_default="tin_tuc",
    )
    payload = Path("data/fixtures/news/vnexpress_tin_moi.xml").read_text(encoding="utf-8")
    records = parse_news_feed(source, payload)

    assert len(records) == 3
    assert records[0].title == "Hà Nội mở thêm tuyến buýt điện nội đô"
    assert records[0].canonical_url.startswith("https://vnexpress.example")
