from __future__ import annotations

from datetime import datetime

from app.models import Article, Source
from app.services.news_service import NewsService


def _create_source(db, source_name: str) -> Source:
    source = Source(
        pipeline_name="news",
        source_name=source_name,
        source_type="rss",
        category_default="tin_tuc",
        base_url="https://example.com",
        config_json={},
    )
    db.add(source)
    db.flush()
    return source


def test_finance_topic_summary_prioritizes_finance_titles(db_session_factory) -> None:
    with db_session_factory() as db:
        source = _create_source(db, "finance_source")
        db.add_all(
            [
                Article(
                    source_id=source.id,
                    category="kinh_te",
                    title="Ngân hàng giảm lãi suất cho vay doanh nghiệp",
                    summary="Bản tin tài chính và ngân hàng trong ngày.",
                    content_clean="Nội dung tài chính chi tiết.",
                    published_at=datetime(2026, 4, 4, 10, 0, 0),
                    canonical_url="https://example.com/finance-1",
                    article_hash="finance-1",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source.id,
                    category="kinh_te",
                    title="Chuẩn bị nhân lực cho Trung tâm Tài chính quốc tế",
                    summary="TP.HCM thúc đẩy tài chính quốc tế.",
                    content_clean="Nội dung về tài chính quốc tế.",
                    published_at=datetime(2026, 4, 4, 9, 0, 0),
                    canonical_url="https://example.com/finance-2",
                    article_hash="finance-2",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source.id,
                    category="giai_tri",
                    title="Phim cổ trang mới ra mắt cuối tuần",
                    summary="Bài giải trí không liên quan tài chính.",
                    content_clean=(
                        "Trong nội dung có nhắc đến kinh tế một lần "
                        "nhưng không phải chủ đề chính."
                    ),
                    published_at=datetime(2026, 4, 4, 11, 0, 0),
                    canonical_url="https://example.com/irrelevant-1",
                    article_hash="irrelevant-1",
                    duplicate_status="unique",
                ),
            ]
        )
        db.commit()

        payload = NewsService(db).summarize_topic(query="tài chính", limit=5)

    titles = [item["title"] for item in payload["items"]]
    assert "Ngân hàng giảm lãi suất cho vay doanh nghiệp" in titles
    assert "Chuẩn bị nhân lực cho Trung tâm Tài chính quốc tế" in titles
    assert "Phim cổ trang mới ra mắt cuối tuần" not in titles


def test_source_compare_education_ignores_summary_only_noise(db_session_factory) -> None:
    with db_session_factory() as db:
        source_a = _create_source(db, "bao_a")
        source_b = _create_source(db, "bao_b")
        db.add_all(
            [
                Article(
                    source_id=source_a.id,
                    category="giao_duc",
                    title="Bộ Giáo dục công bố lịch tuyển sinh mới",
                    summary="Thông tin giáo dục và tuyển sinh.",
                    content_clean="Nội dung giáo dục chi tiết.",
                    published_at=datetime(2026, 4, 4, 10, 0, 0),
                    canonical_url="https://example.com/edu-1",
                    article_hash="edu-1",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source_b.id,
                    category="giao_duc",
                    title="Học đường an toàn trước năm học mới",
                    summary="Bài viết về học sinh và nhà trường.",
                    content_clean="Nội dung học đường.",
                    published_at=datetime(2026, 4, 4, 9, 0, 0),
                    canonical_url="https://example.com/edu-2",
                    article_hash="edu-2",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source_a.id,
                    category="kinh_te",
                    title="Giá nhà tăng ở đô thị lớn",
                    summary="Chi phí giáo dục và y tế tăng theo giá sinh hoạt.",
                    content_clean="Bài này không phải chủ đề giáo dục.",
                    published_at=datetime(2026, 4, 4, 11, 0, 0),
                    canonical_url="https://example.com/noise-1",
                    article_hash="noise-1",
                    duplicate_status="unique",
                ),
            ]
        )
        db.commit()

        payload = NewsService(db).compare_sources(query="giáo dục", limit=10)

    joined_titles = " ".join(
        title
        for comparison in payload["comparisons"]
        for title in comparison["titles"]
    )
    assert "Bộ Giáo dục công bố lịch tuyển sinh mới" in joined_titles
    assert "Học đường an toàn trước năm học mới" in joined_titles
    assert "Giá nhà tăng ở đô thị lớn" not in joined_titles


def test_politics_topic_summary_ignores_discipline_noise(db_session_factory) -> None:
    with db_session_factory() as db:
        source = _create_source(db, "politics_source")
        db.add_all(
            [
                Article(
                    source_id=source.id,
                    category="thoi_su",
                    title="Thủ tướng họp với các địa phương về tăng trưởng",
                    summary="Nội dung điều hành và nghị quyết của Chính phủ.",
                    content_clean="Bài chính trị - điều hành.",
                    published_at=datetime(2026, 4, 4, 10, 0, 0),
                    canonical_url="https://example.com/politics-1",
                    article_hash="politics-1",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source.id,
                    category="thoi_su",
                    title="Thành ủy TP.HCM hoàn thiện dự thảo luật đô thị đặc biệt",
                    summary="Chuẩn bị hồ sơ trình Quốc hội.",
                    content_clean="Bài chính trị - lập pháp.",
                    published_at=datetime(2026, 4, 4, 9, 0, 0),
                    canonical_url="https://example.com/politics-2",
                    article_hash="politics-2",
                    duplicate_status="unique",
                ),
                Article(
                    source_id=source.id,
                    category="giao_duc",
                    title="ĐH Quốc gia siết kỷ luật phòng thi đánh giá năng lực",
                    summary="Bài giáo dục có chữ kỷ luật nhưng không phải chính trị.",
                    content_clean="Bài giáo dục.",
                    published_at=datetime(2026, 4, 4, 11, 0, 0),
                    canonical_url="https://example.com/noise-politics",
                    article_hash="noise-politics",
                    duplicate_status="unique",
                ),
            ]
        )
        db.commit()

        payload = NewsService(db).summarize_topic(query="chính trị", limit=5)

    titles = [item["title"] for item in payload["items"]]
    assert "Thủ tướng họp với các địa phương về tăng trưởng" in titles
    assert "Thành ủy TP.HCM hoàn thiện dự thảo luật đô thị đặc biệt" in titles
    assert "ĐH Quốc gia siết kỷ luật phòng thi đánh giá năng lực" not in titles
