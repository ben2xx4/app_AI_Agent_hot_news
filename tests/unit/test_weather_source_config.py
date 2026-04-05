from __future__ import annotations

from app.pipelines.common.source_loader import load_sources_for_pipeline


def test_weather_sources_include_city_expansion() -> None:
    source_names = {source.name for source in load_sources_for_pipeline("weather")}

    assert {
        "open_meteo_weather_hanoi_live",
        "open_meteo_weather_hcm_live",
        "open_meteo_weather_danang_live",
        "open_meteo_weather_haiphong_live",
        "open_meteo_weather_cantho_live",
        "open_meteo_weather_nhatrang_live",
    }.issubset(source_names)
