from __future__ import annotations

from app.pipelines.common.source_loader import load_sources_for_pipeline


def test_news_sources_include_live_expansion() -> None:
    source_names = {source.name for source in load_sources_for_pipeline("news")}

    assert {
        "vnexpress_rss_tin_moi",
        "vnexpress_rss_thoi_su",
        "vnexpress_rss_kinh_doanh",
        "vnexpress_rss_the_gioi",
        "vnexpress_rss_giao_duc",
        "dantri_rss_tin_moi",
        "dantri_rss_the_gioi",
        "dantri_rss_kinh_doanh",
        "dantri_rss_giao_duc",
        "dantri_rss_the_thao",
        "thanhnien_rss_trang_chu",
        "thanhnien_rss_thoi_su",
        "thanhnien_rss_kinh_te",
        "thanhnien_rss_the_gioi",
        "thanhnien_rss_giao_duc",
        "tuoitre_rss_thoi_su",
    }.issubset(source_names)


def test_all_news_sources_are_capped_to_30_days_or_less() -> None:
    news_sources = load_sources_for_pipeline("news")

    assert news_sources
    assert all(int(source.extra.get("max_age_days", 0)) <= 30 for source in news_sources)
    assert all(int(source.extra.get("max_age_days", 0)) > 0 for source in news_sources)


def test_live_traffic_sources_are_capped_to_14_days() -> None:
    traffic_sources = {
        source.name: source
        for source in load_sources_for_pipeline("traffic")
        if not source.extra.get("demo_only_source")
    }

    assert {"vov_giaothong_traffic_live", "vnexpress_traffic_live"} <= set(traffic_sources)
    assert all(
        int(source.extra.get("max_age_days", 0)) == 14 for source in traffic_sources.values()
    )


def test_policy_sources_do_not_enforce_ingest_age_window() -> None:
    policy_sources = load_sources_for_pipeline("policy")

    assert policy_sources
    assert all(source.extra.get("max_age_days") in {None, ""} for source in policy_sources)
