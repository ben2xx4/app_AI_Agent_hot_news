from __future__ import annotations

from collections import Counter

DEMO_SOURCES = {
    "sjc_gold_prices",
    "petrolimex_fuel_prices",
    "sbv_fx_rates",
    "nchmf_weather_daily",
    "chinhphu_policy_updates",
    "vov_traffic_updates",
}


def should_load_dashboard_payloads(section_key: str | None) -> bool:
    return (section_key or "dashboard") == "dashboard"


def extract_payload_items(payload: dict | None) -> list[dict]:
    return list((payload or {}).get("items", []))


def summarize_sidebar_runtime(
    dataset_overview: list[dict] | None,
    *payloads: dict | None,
) -> tuple[str, str]:
    items = [
        item
        for payload in payloads
        for item in extract_payload_items(payload)
    ]
    if items:
        sources = [
            str(item.get("source", "")).strip()
            for item in items
            if item.get("source")
        ]
        if not sources:
            return "Chưa rõ", "Payload preview hiện tại chưa trả source rõ ràng."

        live_count = sum(source not in DEMO_SOURCES for source in sources)
        demo_count = sum(source in DEMO_SOURCES for source in sources)
        top_source = Counter(sources).most_common(1)[0][0]

        if live_count and demo_count:
            return (
                "Mixed",
                "Preview đang trộn live và demo. "
                f"Source xuất hiện nhiều nhất: {top_source}.",
            )
        if live_count:
            return (
                "Live",
                f"Preview hiện nghiêng về nguồn live. Source nổi bật: {top_source}.",
            )
        return "Demo", f"Preview hiện đang lấy từ bộ demo. Source nổi bật: {top_source}."

    if dataset_overview:
        total_rows = sum(int(item.get("total_rows", 0)) for item in dataset_overview)
        if total_rows > 0:
            return (
                "Database local",
                "Sidebar đang đọc theo database hiện có. "
                "Mở workspace Tổng quan để xem preview dữ liệu live/demo chi tiết hơn.",
            )

    return "Chưa rõ", "Chưa đọc được dữ liệu preview hoặc snapshot database."
