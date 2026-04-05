from __future__ import annotations

from pathlib import Path

from app.pipelines.common.records import SourceDefinition
from app.pipelines.news.parser import parse_news_feed
from app.pipelines.policy.parser import parse_policy_payload
from app.pipelines.price.parser import parse_price_payload
from app.pipelines.traffic.parser import parse_traffic_payload
from app.pipelines.weather.parser import parse_weather_payload

FIXTURE_ROOT = Path("tests/fixtures/live")


def _read_fixture(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def test_parse_tuoitre_rss_with_detail_smoke() -> None:
    source = SourceDefinition(
        name="tuoitre_rss_thoi_su",
        pipeline="news",
        source_type="rss",
        parser="tuoitre_rss_detail",
        category_default="thoi_su",
        extra={"max_items": 3},
    )

    records = parse_news_feed(
        source,
        _read_fixture("tuoitre_rss.xml"),
        detail_fetcher=lambda _url, _source: _read_fixture("tuoitre_article.html"),
    )

    assert len(records) == 1
    assert "Luật Đô thị đặc biệt" in records[0].title
    assert "Quốc hội" in records[0].content_clean
    assert records[0].author == "TIẾN LONG, KỲ PHONG"


def test_parse_vietcombank_fx_xml_smoke() -> None:
    source = SourceDefinition(
        name="vietcombank_fx_rates_live",
        pipeline="price",
        source_type="xml",
        parser="vietcombank_fx_xml",
        extra={"provider_suffix": "vcb", "currencies": ["USD", "EUR"]},
    )

    records = parse_price_payload(source, _read_fixture("vietcombank_fx.xml"))

    assert len(records) == 2
    assert records[0].item_type == "ty_gia"
    assert records[0].item_name.startswith("ty-gia-")
    assert records[1].sell_price is not None


def test_parse_sjc_gold_live_smoke() -> None:
    source = SourceDefinition(
        name="sjc_gold_prices_live",
        pipeline="price",
        source_type="json",
        parser="sjc_gold_json",
        extra={
            "unit": "VND/lượng",
            "type_map": {
                "Vàng SJC 1L, 10L, 1KG": "gia-vang-sjc",
                "Vàng nhẫn SJC 99,99% 1 chỉ, 2 chỉ, 5 chỉ": "gia-vang-nhan-9999",
            },
        },
    )

    records = parse_price_payload(source, _read_fixture("sjc_gold_live.json"))

    assert len(records) == 2
    assert records[0].item_name == "gia-vang-sjc"
    assert records[0].sell_price == 174500000
    assert records[0].unit == "VND/lượng"


def test_parse_petrolimex_fuel_live_smoke() -> None:
    source = SourceDefinition(
        name="petrolimex_fuel_prices_live",
        pipeline="price",
        source_type="json",
        parser="petrolimex_fuel_json",
        extra={
            "item_type": "fuel",
            "region": "Vùng 1",
            "unit": "VND/lít",
            "price_field": "Zone1Price",
            "product_map": {
                "Xăng RON 95-III": "gia-xang-ron95-iii",
                "Xăng E5 RON 92-II": "gia-xang-e5-ron92",
            },
        },
    )

    records = parse_price_payload(source, _read_fixture("petrolimex_fuel_live.json"))

    assert len(records) == 2
    assert records[0].item_name == "gia-xang-ron95-iii"
    assert records[0].sell_price == 26970
    assert records[0].unit == "VND/lít"


def test_parse_sbv_fx_html_smoke() -> None:
    source = SourceDefinition(
        name="sbv_fx_rates_live",
        pipeline="price",
        source_type="html",
        parser="sbv_fx_html",
        extra={
            "item_type": "ty_gia",
            "region": "Viet Nam",
            "currencies": ["USD", "EUR"],
            "item_name_map": {
                "USD": "ty-gia-usd-ban-ra",
                "EUR": "ty-gia-eur-sbv",
            },
            "central_rate_item_name": "ty-gia-usd-trung-tam-sbv",
        },
    )

    records = parse_price_payload(source, _read_fixture("sbv_fx_rates_live.html"))

    assert len(records) == 3
    assert records[0].item_name == "ty-gia-usd-ban-ra"
    assert records[0].buy_price == 23902
    assert records[0].sell_price == 26312
    assert records[0].unit == "VND/USD"
    assert records[-1].item_name == "ty-gia-usd-trung-tam-sbv"
    assert records[-1].sell_price == 25107


def test_parse_open_meteo_payload_smoke() -> None:
    source = SourceDefinition(
        name="open_meteo_weather_hanoi_live",
        pipeline="weather",
        source_type="json",
        parser="open_meteo_forecast",
        extra={"location_name": "Hà Nội"},
    )

    records = parse_weather_payload(source, _read_fixture("open_meteo_hanoi.json"))

    assert len(records) == 1
    assert records[0].location == "Hà Nội"
    assert records[0].weather_text == "Nhiều mây"
    assert records[0].humidity is not None


def test_parse_open_meteo_payload_can_use_new_city_name() -> None:
    source = SourceDefinition(
        name="open_meteo_weather_cantho_live",
        pipeline="weather",
        source_type="json",
        parser="open_meteo_forecast",
        extra={"location_name": "Cần Thơ"},
    )

    records = parse_weather_payload(source, _read_fixture("open_meteo_hanoi.json"))

    assert len(records) == 1
    assert records[0].location == "Cần Thơ"


def test_parse_congbao_listing_smoke() -> None:
    source = SourceDefinition(
        name="congbao_policy_updates_live",
        pipeline="policy",
        source_type="html",
        parser="congbao_listing_html",
        category_default="chinh_sach",
        url="https://congbao.chinhphu.vn/van-ban-dang-cong-bao/chinh-phu-c1.htm",
        extra={"site_root": "https://congbao.chinhphu.vn", "max_items": 3},
    )

    records = parse_policy_payload(
        source,
        _read_fixture("congbao_listing.html"),
        detail_fetcher=lambda _url, _source: _read_fixture("congbao_detail.html"),
    )

    assert len(records) == 1
    assert records[0].doc_number == "79/2026/NĐ-CP"
    assert records[0].issuing_agency == "CHÍNH PHỦ"
    assert records[0].field == "giao thông"


def test_parse_vov_listing_smoke() -> None:
    source = SourceDefinition(
        name="vov_giaothong_traffic_live",
        pipeline="traffic",
        source_type="html",
        parser="vov_listing_html",
        url="https://vovgiaothong.vn/giao-thong",
        extra={"site_root": "https://vovgiaothong.vn", "max_items": 3},
    )

    records = parse_traffic_payload(
        source,
        _read_fixture("vov_listing.html"),
        detail_fetcher=lambda _url, _source: _read_fixture("vov_detail.html"),
    )

    assert len(records) == 1
    assert records[0].location == "Hà Nội"
    assert records[0].event_type == "tai_nan"
    assert "phân luồng" in (records[0].description or "")


def test_parse_vov_listing_skips_non_traffic_article() -> None:
    source = SourceDefinition(
        name="vov_giaothong_traffic_live",
        pipeline="traffic",
        source_type="html",
        parser="vov_listing_html",
        url="https://vovgiaothong.vn/giao-thong",
        extra={"site_root": "https://vovgiaothong.vn", "max_items": 3},
    )

    records = parse_traffic_payload(
        source,
        _read_fixture("vov_listing.html"),
        detail_fetcher=lambda _url, _source: _read_fixture("vov_non_traffic_detail.html"),
    )

    assert records == []


def test_parse_vnexpress_traffic_listing_smoke() -> None:
    source = SourceDefinition(
        name="vnexpress_traffic_live",
        pipeline="traffic",
        source_type="html",
        parser="vnexpress_listing_html",
        url="https://vnexpress.net/thoi-su/giao-thong",
        extra={"site_root": "https://vnexpress.net", "max_items": 3},
    )

    records = parse_traffic_payload(
        source,
        _read_fixture("vnexpress_traffic_listing.html"),
        detail_fetcher=lambda _url, _source: _read_fixture("vnexpress_traffic_detail.html"),
    )

    assert len(records) == 1
    assert records[0].location == "TP.HCM"
    assert records[0].event_type == "un_tac"
    assert "container" in (records[0].description or "")
