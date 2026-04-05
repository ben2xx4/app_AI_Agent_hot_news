from __future__ import annotations

from app.ui.presentation import (
    build_dataset_overview_chart_frame,
    build_news_board_model,
    build_news_source_chart_frame,
    build_weather_chart_frame,
    format_ui_source_label,
)


def test_format_ui_source_label_maps_common_sources_to_readable_labels() -> None:
    assert format_ui_source_label("thanhnien_rss_thoi_su") == "Thanh Niên · Thời sự"
    assert format_ui_source_label("vietcombank_fx_rates_live") == "Vietcombank"
    assert format_ui_source_label("open_meteo_weather_hanoi_live") == "Open-Meteo"


def test_format_ui_source_label_falls_back_to_title_case_for_unknown_source() -> None:
    assert format_ui_source_label("custom_feed_alpha") == "Custom Feed Alpha"


def test_build_news_board_model_limits_secondary_items_and_counts_sources() -> None:
    model = build_news_board_model(
        [
            {"title": "Tin 1", "source": "thanhnien_rss_thoi_su"},
            {"title": "Tin 2", "source": "vnexpress_rss_the_gioi"},
            {"title": "Tin 3", "source": "dantri_rss_giao_duc"},
            {"title": "Tin 4", "source": "dantri_rss_giao_duc"},
            {"title": "Tin 5", "source": "tuoitre_rss_thoi_su"},
            {"title": "Tin 6", "source": "vnexpress_rss_the_gioi"},
        ],
        secondary_limit=4,
    )

    assert model.featured is not None
    assert model.featured["title"] == "Tin 1"
    assert len(model.secondary_items) == 4
    assert model.total_items == 6
    assert model.source_count == 4


def test_build_dataset_overview_chart_frame_returns_expected_columns() -> None:
    frame = build_dataset_overview_chart_frame(
        [
            {"title": "Tin tức", "total_rows": 120},
            {"title": "Giá cả", "total_rows": 24},
        ]
    )

    assert list(frame.columns) == ["Nhóm dữ liệu", "Số bản ghi"]
    assert frame.iloc[0]["Nhóm dữ liệu"] == "Tin tức"
    assert int(frame.iloc[1]["Số bản ghi"]) == 24


def test_build_news_source_chart_frame_groups_sources() -> None:
    frame = build_news_source_chart_frame(
        [
            {"source": "thanhnien_rss_thoi_su"},
            {"source": "thanhnien_rss_thoi_su"},
            {"source": "vnexpress_rss_the_gioi"},
        ]
    )

    assert list(frame.columns) == ["Nguồn", "Số bài"]
    assert frame.iloc[0]["Nguồn"] == "Thanh Niên · Thời sự"
    assert int(frame.iloc[0]["Số bài"]) == 2


def test_build_weather_chart_frame_returns_min_max_for_locations() -> None:
    frame = build_weather_chart_frame(
        [
            ("Hà Nội", {"min_temp": 23.5, "max_temp": 31.2}, None),
            ("TP.HCM", {"min_temp": 26.0, "max_temp": 34.5}, None),
        ]
    )

    assert list(frame.columns) == ["Địa điểm", "Nhiệt độ thấp", "Nhiệt độ cao"]
    assert frame.iloc[0]["Địa điểm"] == "Hà Nội"
    assert float(frame.iloc[1]["Nhiệt độ cao"]) == 34.5
