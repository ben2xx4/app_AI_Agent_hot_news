from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.models import PriceSnapshot, Source
from app.services.price_service import PriceService


def _create_source(db, source_name: str, *, demo_only: bool) -> Source:
    source = Source(
        pipeline_name="price",
        source_name=source_name,
        source_type="json",
        category_default="price",
        base_url="https://example.com",
        config_json={"demo_only_source": demo_only},
    )
    db.add(source)
    db.flush()
    return source


def test_get_latest_price_prefers_live_source_over_newer_demo(db_session_factory) -> None:
    with db_session_factory() as db:
        demo_source = _create_source(db, "sjc_gold_prices", demo_only=True)
        live_source = _create_source(db, "sjc_gold_prices_live", demo_only=False)
        db.add_all(
            [
                PriceSnapshot(
                    source_id=live_source.id,
                    item_type="gia_vang",
                    item_name="gia-vang-sjc",
                    region="Viet Nam",
                    sell_price=Decimal("174500000"),
                    unit="VND/lượng",
                    effective_at=datetime(2026, 4, 4, 8, 0, 0),
                ),
                PriceSnapshot(
                    source_id=demo_source.id,
                    item_type="gia_vang",
                    item_name="gia-vang-sjc",
                    region="Viet Nam",
                    sell_price=Decimal("82500000"),
                    unit="VND/lượng",
                    effective_at=datetime(2026, 4, 4, 9, 0, 0),
                ),
            ]
        )
        db.commit()

        payload = PriceService(db).get_latest_price(item_name="gia-vang-sjc")

    assert payload["items"][0]["source"] == "sjc_gold_prices_live"
    assert payload["items"][0]["display_value"] == "174.500.000 VNĐ/lượng"


def test_compare_price_prefers_live_history_over_demo_history(db_session_factory) -> None:
    with db_session_factory() as db:
        demo_source = _create_source(db, "petrolimex_fuel_prices", demo_only=True)
        live_source = _create_source(db, "petrolimex_fuel_prices_live", demo_only=False)
        db.add_all(
            [
                PriceSnapshot(
                    source_id=live_source.id,
                    item_type="fuel",
                    item_name="gia-xang-ron95-iii",
                    region="Vùng 1",
                    sell_price=Decimal("26970"),
                    unit="VND/lít",
                    effective_at=datetime(2026, 4, 4, 8, 0, 0),
                ),
                PriceSnapshot(
                    source_id=live_source.id,
                    item_type="fuel",
                    item_name="gia-xang-ron95-iii",
                    region="Vùng 1",
                    sell_price=Decimal("26880"),
                    unit="VND/lít",
                    effective_at=datetime(2026, 4, 3, 8, 0, 0),
                ),
                PriceSnapshot(
                    source_id=demo_source.id,
                    item_type="fuel",
                    item_name="gia-xang-ron95-iii",
                    region="Vùng 1",
                    sell_price=Decimal("24500"),
                    unit="VND/lít",
                    effective_at=datetime(2026, 4, 4, 9, 0, 0),
                ),
            ]
        )
        db.commit()

        payload = PriceService(db).compare_price(item_name="gia-xang-ron95-iii")

    assert payload["current"]["source"] == "petrolimex_fuel_prices_live"
    assert payload["previous"]["source"] == "petrolimex_fuel_prices_live"
    assert payload["current"]["display_value"] == "26.970 VNĐ/lít"
    assert payload["previous"]["display_value"] == "26.880 VNĐ/lít"


def test_get_latest_price_falls_back_to_demo_when_live_is_missing(db_session_factory) -> None:
    with db_session_factory() as db:
        demo_source = _create_source(db, "sbv_fx_rates", demo_only=True)
        db.add(
            PriceSnapshot(
                source_id=demo_source.id,
                item_type="ty_gia",
                item_name="ty-gia-usd-ban-ra",
                region="Viet Nam",
                sell_price=Decimal("25500"),
                unit="VND/USD",
                effective_at=datetime(2026, 4, 4, 9, 0, 0),
            )
        )
        db.commit()

        payload = PriceService(db).get_latest_price(item_name="ty-gia-usd-ban-ra")

    assert payload["items"][0]["source"] == "sbv_fx_rates"
    assert payload["items"][0]["display_value"] == "25.500 VNĐ/USD"
