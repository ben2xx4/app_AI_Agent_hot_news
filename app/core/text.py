from __future__ import annotations

import re
import unicodedata
from decimal import Decimal

PRICE_DISPLAY_NAMES = {
    "gia-vang-sjc": "Giá vàng SJC",
    "gia-vang-nhan-9999": "Giá vàng nhẫn 9999",
    "gia-xang-ron95-iii": "Giá xăng RON95-III",
    "gia-xang-e5-ron92": "Giá xăng E5 RON92",
    "gia-xang-ron95-v": "Giá xăng RON95-V",
    "gia-xang-e10-ron95-iii": "Giá xăng E10 RON95-III",
    "gia-dau-do-0001s-v": "Giá dầu DO 0,001S-V",
    "gia-dau-do-005s-ii": "Giá dầu DO 0,05S-II",
    "gia-dau-hoa-2k": "Giá dầu hỏa 2-K",
    "ty-gia-usd-ban-ra": "Tỷ giá USD bán ra",
    "ty-gia-usd-trung-tam-sbv": "Tỷ giá trung tâm USD",
    "ty-gia-usd-vcb": "Tỷ giá USD Vietcombank",
    "ty-gia-eur-sbv": "Tỷ giá EUR NHNN",
    "ty-gia-eur-vcb": "Tỷ giá EUR Vietcombank",
    "ty-gia-jpy-sbv": "Tỷ giá JPY NHNN",
    "ty-gia-jpy-vcb": "Tỷ giá JPY Vietcombank",
    "ty-gia-gbp-sbv": "Tỷ giá GBP NHNN",
    "ty-gia-gbp-vcb": "Tỷ giá GBP Vietcombank",
}

PRICE_UNIT_DISPLAY_NAMES = {
    "VND/luong": "VNĐ/lượng",
    "VND/lượng": "VNĐ/lượng",
    "VND/lit": "VNĐ/lít",
    "VND/lít": "VNĐ/lít",
    "VND/USD": "VNĐ/USD",
    "VND/EUR": "VNĐ/EUR",
    "VND/JPY": "VNĐ/JPY",
    "VND/GBP": "VNĐ/GBP",
    "VND": "VNĐ",
}

LOCATION_DISPLAY_NAMES = {
    "Ha Noi": "Hà Nội",
    "TP.HCM": "TP.HCM",
    "Da Nang": "Đà Nẵng",
    "Việt Nam": "Việt Nam",
}

FIELD_DISPLAY_NAMES = {
    "chinh tri": "chính trị",
    "giao duc": "giáo dục",
    "y te": "y tế",
    "tai chinh": "tài chính",
    "kinh te": "kinh tế",
    "giao thong": "giao thông",
    "giai tri": "giải trí",
    "suc khoe": "sức khỏe",
}

POLICY_QUERY_ALIASES = {
    "hoc duong": [
        "hoc duong",
        "giao duc",
        "tuyen sinh",
        "hoc sinh",
        "nha truong",
    ],
}

NEWS_TOPIC_ALIASES = {
    "chinh tri": [
        "chinh tri",
        "quoc hoi",
        "thanh uy",
        "bi thu",
        "thu tuong",
        "bo chinh tri",
        "nghi dinh",
        "nghi quyet",
        "du thao luat",
    ],
    "tai chinh": [
        "tai chinh",
        "kinh te",
        "gia vang",
        "ty gia",
        "ngan hang",
        "thuong mai",
        "thue",
        "gia cuoc",
        "nhien lieu",
        "sacombank",
    ],
    "kinh te": [
        "kinh te",
        "tai chinh",
        "gia cuoc",
        "gia nhien lieu",
        "ngan hang",
        "thuong mai",
    ],
    "giao duc": [
        "giao duc",
        "hoc duong",
        "tuyen sinh",
        "bo giao duc",
        "truong hoc",
        "danh gia nang luc",
    ],
}

TREND_DISPLAY_NAMES = {
    "tang": "tăng",
    "giam": "giảm",
    "khong_doi": "không đổi",
    "no_data": "chưa có dữ liệu",
}


def fold_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    stripped = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    stripped = re.sub(r"[^a-z0-9]+", " ", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def contains_folded(text: str | None, query: str | None) -> bool:
    folded_query = fold_text(query)
    if not folded_query:
        return True
    return folded_query in fold_text(text)


def display_location(location: str | None) -> str | None:
    if not location:
        return location
    return LOCATION_DISPLAY_NAMES.get(location, location)


def display_price_name(item_name: str) -> str:
    return PRICE_DISPLAY_NAMES.get(item_name, item_name.replace("-", " ").title())


def display_price_unit(unit: str | None) -> str | None:
    if not unit:
        return unit
    return PRICE_UNIT_DISPLAY_NAMES.get(unit, unit)


def format_price_amount(value: Decimal | int | float | None) -> str | None:
    if value is None:
        return None
    decimal_value = Decimal(str(value))
    if decimal_value == decimal_value.to_integral():
        return f"{int(decimal_value):,}".replace(",", ".")
    integer_part, fractional_part = f"{decimal_value:.2f}".split(".")
    integer_formatted = f"{int(integer_part):,}".replace(",", ".")
    return f"{integer_formatted},{fractional_part}"


def format_price_with_unit(value: Decimal | int | float | None, unit: str | None) -> str | None:
    formatted_value = format_price_amount(value)
    formatted_unit = display_price_unit(unit)
    if not formatted_value:
        return None
    if not formatted_unit:
        return formatted_value
    return f"{formatted_value} {formatted_unit}"


def display_field(field: str | None) -> str | None:
    if not field:
        return field
    return FIELD_DISPLAY_NAMES.get(fold_text(field), field)


def display_trend(trend: str) -> str:
    return TREND_DISPLAY_NAMES.get(trend, trend)


def expand_news_topic_query(query: str | None) -> list[str]:
    folded = fold_text(query)
    if not folded:
        return []
    aliases = NEWS_TOPIC_ALIASES.get(folded, [])
    ordered = [folded, *aliases]
    seen: set[str] = set()
    expanded: list[str] = []
    for item in ordered:
        if not item or item in seen:
            continue
        seen.add(item)
        expanded.append(item)
    return expanded


def expand_policy_query(query: str | None) -> list[str]:
    folded = fold_text(query)
    if not folded:
        return []
    aliases = POLICY_QUERY_ALIASES.get(folded, [])
    ordered = [folded, *aliases]
    seen: set[str] = set()
    expanded: list[str] = []
    for item in ordered:
        if not item or item in seen:
            continue
        seen.add(item)
        expanded.append(item)
    return expanded
