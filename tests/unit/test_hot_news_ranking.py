from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from app.core.news_hotness import rank_hot_news_rows, score_hot_news_candidate


def _row(
    row_id: int,
    source_id: int,
    title: str,
    *,
    summary: str = "",
    category: str = "tin_tuc",
    published_at: datetime | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=row_id,
        source_id=source_id,
        title=title,
        summary=summary,
        category=category,
        published_at=published_at,
        duplicate_status="unique",
    )


def test_score_hot_news_candidate_penalizes_soft_story_titles() -> None:
    now = datetime(2026, 4, 5, 2, 46, 0)
    soft_score = score_hot_news_candidate(
        title="Lợi ích sức khỏe của hạt lanh",
        summary="Mẹo ăn uống mỗi ngày",
        category="tin_tuc",
        source_name="vnexpress_rss_tin_moi",
        published_at=now - timedelta(hours=1),
        now=now,
    )
    hard_score = score_hot_news_candidate(
        title="Chính phủ điều chỉnh thuế với xăng dầu từ tuần tới",
        summary="Bộ Tài chính công bố nghị định mới",
        category="kinh_doanh",
        source_name="vnexpress_rss_kinh_doanh",
        published_at=now - timedelta(hours=2),
        now=now,
    )

    assert hard_score > soft_score


def test_rank_hot_news_rows_prioritizes_hard_news_and_source_diversity() -> None:
    now = datetime(2026, 4, 5, 2, 46, 0)
    rows = [
        _row(
            1,
            101,
            "Lợi ích sức khỏe của hạt lanh",
            summary="Mẹo ăn uống mỗi ngày",
            category="tin_tuc",
            published_at=now - timedelta(minutes=20),
        ),
        _row(
            2,
            102,
            "Chính phủ điều chỉnh thuế với xăng dầu từ tuần tới",
            summary="Bộ Tài chính công bố nghị định mới",
            category="kinh_doanh",
            published_at=now - timedelta(hours=2),
        ),
        _row(
            3,
            103,
            "Hà Nội phân luồng giao thông quanh hồ Hoàn Kiếm",
            summary="Kế hoạch cấm đường phục vụ sự kiện cuối tuần",
            category="thoi_su",
            published_at=now - timedelta(hours=1),
        ),
        _row(
            4,
            103,
            "Cánh rừng gỗ quý được gìn giữ suốt 6 thế kỷ",
            category="the_gioi",
            published_at=now - timedelta(minutes=10),
        ),
    ]
    source_name_map = {
        101: "vnexpress_rss_tin_moi",
        102: "vnexpress_rss_kinh_doanh",
        103: "tuoitre_rss_thoi_su",
    }

    ranked = rank_hot_news_rows(rows, source_name_map=source_name_map, limit=3, now=now)
    titles = [row.title for row in ranked]

    assert titles[0] == "Hà Nội phân luồng giao thông quanh hồ Hoàn Kiếm"
    assert "Chính phủ điều chỉnh thuế với xăng dầu từ tuần tới" in titles
    assert "Lợi ích sức khỏe của hạt lanh" not in titles[:2]
