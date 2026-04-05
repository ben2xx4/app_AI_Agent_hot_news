from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import unescape

import pandas as pd

SOURCE_LABELS = {
    "vnexpress_rss_tin_moi": "VnExpress · Tin mới",
    "vnexpress_rss_thoi_su": "VnExpress · Thời sự",
    "vnexpress_rss_kinh_doanh": "VnExpress · Kinh doanh",
    "vnexpress_rss_the_gioi": "VnExpress · Thế giới",
    "vnexpress_rss_giao_duc": "VnExpress · Giáo dục",
    "dantri_rss_tin_moi": "Dân Trí · Tin mới",
    "dantri_rss_the_gioi": "Dân Trí · Thế giới",
    "dantri_rss_kinh_doanh": "Dân Trí · Kinh doanh",
    "dantri_rss_giao_duc": "Dân Trí · Giáo dục",
    "dantri_rss_the_thao": "Dân Trí · Thể thao",
    "thanhnien_rss_trang_chu": "Thanh Niên · Trang chủ",
    "thanhnien_rss_thoi_su": "Thanh Niên · Thời sự",
    "thanhnien_rss_kinh_te": "Thanh Niên · Kinh tế",
    "thanhnien_rss_the_gioi": "Thanh Niên · Thế giới",
    "thanhnien_rss_giao_duc": "Thanh Niên · Giáo dục",
    "tuoitre_rss_thoi_su": "Tuổi Trẻ · Thời sự",
    "sjc_gold_prices_live": "SJC",
    "petrolimex_fuel_prices_live": "Petrolimex",
    "sbv_fx_rates_live": "Ngân hàng Nhà nước",
    "vietcombank_fx_rates_live": "Vietcombank",
    "open_meteo_weather_hanoi_live": "Open-Meteo",
    "open_meteo_weather_hcm_live": "Open-Meteo",
    "open_meteo_weather_danang_live": "Open-Meteo",
    "open_meteo_weather_haiphong_live": "Open-Meteo",
    "open_meteo_weather_cantho_live": "Open-Meteo",
    "open_meteo_weather_nhatrang_live": "Open-Meteo",
    "congbao_policy_updates_live": "Công báo Chính phủ",
    "congbao_thu_tuong_policy_live": "Thủ tướng Chính phủ",
    "congbao_quoc_hoi_policy_live": "Quốc hội",
    "vov_giaothong_traffic_live": "VOV Giao thông",
    "vnexpress_traffic_live": "VnExpress · Giao thông",
}


@dataclass(frozen=True)
class NewsBoardModel:
    featured: Mapping[str, object] | None
    secondary_items: tuple[Mapping[str, object], ...]
    total_items: int
    source_count: int


def format_ui_source_label(source: str | None) -> str:
    if not source:
        return "Không rõ nguồn"

    clean_source = unescape(source).strip()
    if not clean_source:
        return "Không rõ nguồn"

    lowered = clean_source.casefold()
    if lowered in SOURCE_LABELS:
        return SOURCE_LABELS[lowered]

    return clean_source.replace("_", " ").strip().title()


def build_news_board_model(
    items: Sequence[Mapping[str, object]],
    *,
    secondary_limit: int = 4,
) -> NewsBoardModel:
    clean_items = tuple(item for item in items if item.get("title"))
    if not clean_items:
        return NewsBoardModel(
            featured=None,
            secondary_items=(),
            total_items=0,
            source_count=0,
        )

    source_count = len(
        {
            format_ui_source_label(str(item.get("source") or ""))
            for item in clean_items
            if item.get("source")
        }
    )
    return NewsBoardModel(
        featured=clean_items[0],
        secondary_items=clean_items[1 : 1 + secondary_limit],
        total_items=len(clean_items),
        source_count=source_count,
    )


def build_dataset_overview_chart_frame(
    dataset_overview: Sequence[Mapping[str, object]],
) -> pd.DataFrame:
    rows = [
        {
            "Nhóm dữ liệu": str(item.get("title") or item.get("key") or "Không rõ"),
            "Số bản ghi": int(item.get("total_rows", 0) or 0),
        }
        for item in dataset_overview
    ]
    if not rows:
        return pd.DataFrame(columns=["Nhóm dữ liệu", "Số bản ghi"])
    return pd.DataFrame(rows)


def build_news_source_chart_frame(items: Sequence[Mapping[str, object]]) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for item in items:
        source_label = format_ui_source_label(str(item.get("source") or "Không rõ nguồn"))
        counts[source_label] = counts.get(source_label, 0) + 1
    rows = [
        {"Nguồn": source, "Số bài": count}
        for source, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
    ]
    if not rows:
        return pd.DataFrame(columns=["Nguồn", "Số bài"])
    return pd.DataFrame(rows)


def build_weather_chart_frame(
    weather_payloads: Sequence[tuple[str, Mapping[str, object] | None, str | None]],
) -> pd.DataFrame:
    rows = []
    for location, payload, _error in weather_payloads:
        if not payload:
            continue
        min_temp = payload.get("min_temp")
        max_temp = payload.get("max_temp")
        if min_temp is None and max_temp is None:
            continue
        rows.append(
            {
                "Địa điểm": location,
                "Nhiệt độ thấp": float(min_temp) if min_temp is not None else None,
                "Nhiệt độ cao": float(max_temp) if max_temp is not None else None,
            }
        )
    if not rows:
        return pd.DataFrame(columns=["Địa điểm", "Nhiệt độ thấp", "Nhiệt độ cao"])
    return pd.DataFrame(rows)
