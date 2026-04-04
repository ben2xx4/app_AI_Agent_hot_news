from __future__ import annotations

import json
from decimal import Decimal

from app.pipelines.common.processing import parse_datetime
from app.pipelines.common.records import SourceDefinition, WeatherRecord


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


WMO_CODE_MAP = {
    0: "Trời quang",
    1: "Ít mây",
    2: "Có mây",
    3: "Nhiều mây",
    45: "Sương mù",
    48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn",
    55: "Mưa phùn dày",
    61: "Mưa nhẹ",
    63: "Mưa vừa",
    65: "Mưa to",
    71: "Tuyết nhẹ",
    80: "Mưa rào nhẹ",
    81: "Mưa rào",
    82: "Mưa rào to",
    95: "Dông",
    96: "Dông mưa đá nhẹ",
    99: "Dông mưa đá mạnh",
}


def _map_weather_text(weather_code: object) -> str | None:
    if weather_code in (None, ""):
        return None
    try:
        code = int(weather_code)
    except (TypeError, ValueError):
        return None
    return WMO_CODE_MAP.get(code, f"Mã thời tiết {code}")


def _build_warning(weather_code: object) -> str | None:
    try:
        code = int(weather_code)
    except (TypeError, ValueError):
        return None
    if code in {95, 96, 99}:
        return "Có khả năng dông hoặc thời tiết nguy hiểm."
    if code in {65, 82}:
        return "Có mưa lớn, cần theo dõi cập nhật mới."
    return None


def _parse_open_meteo_payload(source: SourceDefinition, payload: str) -> list[WeatherRecord]:
    data = json.loads(payload)
    current = data.get("current", {})
    daily = data.get("daily", {})
    times = daily.get("time", [])
    first_index = 0 if times else None
    weather_code = current.get("weather_code")
    if first_index is not None:
        daily_codes = daily.get("weather_code", [])
        if daily_codes:
            weather_code = daily_codes[first_index]

    record = WeatherRecord(
        location=str(source.extra.get("location_name", "Hà Nội")),
        forecast_time=parse_datetime(current.get("time")),
        min_temp=_to_decimal(daily.get("temperature_2m_min", [None])[0] if times else None),
        max_temp=_to_decimal(daily.get("temperature_2m_max", [None])[0] if times else None),
        humidity=_to_decimal(current.get("relative_humidity_2m")),
        wind=(
            f"{current.get('wind_speed_10m')} km/h"
            if current.get("wind_speed_10m") is not None
            else None
        ),
        weather_text=_map_weather_text(weather_code),
        warning_text=_build_warning(weather_code),
    )
    return [record]


def parse_weather_payload(source: SourceDefinition, payload: str) -> list[WeatherRecord]:
    if source.parser == "open_meteo_forecast":
        return _parse_open_meteo_payload(source, payload)

    data = json.loads(payload)
    rows = data.get("records", data if isinstance(data, list) else [])

    records: list[WeatherRecord] = []
    for row in rows:
        records.append(
            WeatherRecord(
                location=row["location"],
                forecast_time=parse_datetime(row.get("forecast_time")),
                min_temp=_to_decimal(row.get("min_temp")),
                max_temp=_to_decimal(row.get("max_temp")),
                humidity=_to_decimal(row.get("humidity")),
                wind=row.get("wind"),
                weather_text=row.get("weather_text"),
                warning_text=row.get("warning_text"),
            )
        )
    return records
