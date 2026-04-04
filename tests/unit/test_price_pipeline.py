from __future__ import annotations

from pathlib import Path

from app.pipelines.common.records import SourceDefinition
from app.pipelines.policy.pipeline import PolicyPipeline
from app.pipelines.price.parser import parse_price_payload
from app.pipelines.price.pipeline import PricePipeline
from app.pipelines.traffic.pipeline import TrafficPipeline
from app.pipelines.weather.pipeline import WeatherPipeline


def test_parse_price_payload_fixture() -> None:
    source = SourceDefinition(name="sjc_gold_prices", pipeline="price", source_type="json")
    payload = Path("data/fixtures/price/gold_prices.json").read_text(encoding="utf-8")
    records = parse_price_payload(source, payload)

    assert len(records) == 3
    assert records[0].item_name == "gia-vang-sjc"
    assert records[0].sell_price == 82500000


def test_demo_gold_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = PricePipeline(demo_only=False, source_names={"sjc_gold_prices"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "sjc_gold_prices"
    assert summaries[0].status == "skipped"
    assert summaries[0].total_success == 0


def test_demo_fuel_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = PricePipeline(demo_only=False, source_names={"petrolimex_fuel_prices"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "petrolimex_fuel_prices"
    assert summaries[0].status == "skipped"


def test_demo_sbv_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = PricePipeline(demo_only=False, source_names={"sbv_fx_rates"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "sbv_fx_rates"
    assert summaries[0].status == "skipped"


def test_demo_weather_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = WeatherPipeline(demo_only=False, source_names={"nchmf_weather_daily"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "nchmf_weather_daily"
    assert summaries[0].status == "skipped"


def test_demo_policy_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = PolicyPipeline(demo_only=False, source_names={"chinhphu_policy_updates"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "chinhphu_policy_updates"
    assert summaries[0].status == "skipped"


def test_demo_traffic_source_is_skipped_in_live_mode(db_session_factory) -> None:
    from app.db.session import get_engine, get_session_factory, set_session_factory_override

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    set_session_factory_override(db_session_factory)

    summaries = TrafficPipeline(demo_only=False, source_names={"vov_traffic_updates"}).run()

    assert len(summaries) == 1
    assert summaries[0].source_name == "vov_traffic_updates"
    assert summaries[0].status == "skipped"
