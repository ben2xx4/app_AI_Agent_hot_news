from __future__ import annotations

import json
import sys

from app.pipelines.common.records import PipelineRunSummary
from scripts import refresh_live_prices as refresh_live_prices_script


class FakePricePipeline:
    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        self.demo_only = demo_only
        self.source_names = source_names or set()

    def run(self) -> list[PipelineRunSummary]:
        return [
            PipelineRunSummary(
                pipeline="price",
                source_name=next(iter(self.source_names or {"sjc_gold_prices_live"})),
                total_fetched=2,
                total_success=2,
                total_failed=0,
                status="success",
                used_demo=False,
                error_message=None,
            )
        ]


def test_refresh_live_prices_main_runs_pipeline_in_live_mode(monkeypatch, capsys) -> None:
    observed: dict[str, object] = {}

    def fake_ensure_sqlite_schema() -> None:
        observed["schema_checked"] = True

    class ObservedPricePipeline(FakePricePipeline):
        def __init__(
            self,
            *,
            demo_only: bool = False,
            source_names: set[str] | None = None,
        ) -> None:
            observed["demo_only"] = demo_only
            observed["source_names"] = source_names
            super().__init__(demo_only=demo_only, source_names=source_names)

    monkeypatch.setattr(
        refresh_live_prices_script,
        "ensure_sqlite_schema",
        fake_ensure_sqlite_schema,
    )
    monkeypatch.setattr(refresh_live_prices_script, "PricePipeline", ObservedPricePipeline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "refresh_live_prices.py",
            "--source",
            "sjc_gold_prices_live",
            "--source",
            "sbv_fx_rates_live",
        ],
    )

    refresh_live_prices_script.main()
    payload = json.loads(capsys.readouterr().out)

    assert observed["schema_checked"] is True
    assert observed["demo_only"] is False
    assert observed["source_names"] == {"sjc_gold_prices_live", "sbv_fx_rates_live"}
    assert payload["summaries"][0]["pipeline"] == "price"
    assert payload["summaries"][0]["used_demo"] is False
