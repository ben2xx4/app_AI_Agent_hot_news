from __future__ import annotations

from datetime import datetime
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


def test_parse_news_feed_skips_articles_older_than_max_age_days() -> None:
    source = SourceDefinition(
        name="news_window_source",
        pipeline="news",
        source_type="rss",
        category_default="tin_tuc",
        extra={"max_age_days": 30},
    )
    payload = """
    <rss version="2.0">
      <channel>
        <title>Tin mới</title>
        <item>
          <title>Bài còn trong cửa sổ</title>
          <link>https://example.com/within-window</link>
          <pubDate>Tue, 25 Mar 2026 09:00:00 GMT</pubDate>
          <description>Mô tả mới</description>
        </item>
        <item>
          <title>Bài quá cũ</title>
          <link>https://example.com/older-than-window</link>
          <pubDate>Wed, 12 Feb 2026 09:00:00 GMT</pubDate>
          <description>Mô tả cũ</description>
        </item>
      </channel>
    </rss>
    """

    records = parse_news_feed(
        source,
        payload,
        now_provider=lambda: datetime(2026, 4, 4, 12, 0, 0),
    )

    assert len(records) == 1
    assert records[0].title == "Bài còn trong cửa sổ"


def test_parse_news_feed_respects_max_items_after_age_filter() -> None:
    source = SourceDefinition(
        name="news_max_items_source",
        pipeline="news",
        source_type="rss",
        category_default="tin_tuc",
        extra={"max_age_days": 30, "max_items": 2},
    )
    payload = """
    <rss version="2.0">
      <channel>
        <title>Tin mới</title>
        <item>
          <title>Bài quá cũ</title>
          <link>https://example.com/too-old</link>
          <pubDate>Wed, 12 Feb 2026 09:00:00 GMT</pubDate>
          <description>Mô tả cũ</description>
        </item>
        <item>
          <title>Bài mới 1</title>
          <link>https://example.com/recent-1</link>
          <pubDate>Thu, 03 Apr 2026 08:30:00 GMT</pubDate>
          <description>Mô tả 1</description>
        </item>
        <item>
          <title>Bài mới 2</title>
          <link>https://example.com/recent-2</link>
          <pubDate>Fri, 04 Apr 2026 07:15:00 GMT</pubDate>
          <description>Mô tả 2</description>
        </item>
        <item>
          <title>Bài mới 3</title>
          <link>https://example.com/recent-3</link>
          <pubDate>Fri, 04 Apr 2026 07:45:00 GMT</pubDate>
          <description>Mô tả 3</description>
        </item>
      </channel>
    </rss>
    """

    records = parse_news_feed(
        source,
        payload,
        now_provider=lambda: datetime(2026, 4, 4, 12, 0, 0),
    )

    assert len(records) == 2
    assert [record.title for record in records] == ["Bài mới 1", "Bài mới 2"]
