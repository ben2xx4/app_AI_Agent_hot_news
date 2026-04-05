from __future__ import annotations

import json
import sys

from app.pipelines.common.records import PipelineRunSummary
from scripts import refresh_live_data as refresh_live_data_script


class FakePipeline:
    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        self.demo_only = demo_only
        self.source_names = source_names or set()

    def run(self) -> list[PipelineRunSummary]:
        return [
            PipelineRunSummary(
                pipeline="news",
                source_name="vnexpress_rss_tin_moi",
                total_fetched=5,
                total_success=5,
                total_failed=0,
                status="success",
                used_demo=False,
                error_message=None,
            )
        ]


def test_refresh_live_data_main_runs_selected_pipelines(monkeypatch, capsys) -> None:
    observed: dict[str, object] = {"pipelines": []}

    def fake_ensure_sqlite_schema() -> None:
        observed["schema_checked"] = True

    class ObservedPipeline(FakePipeline):
        def __init__(
            self,
            *,
            demo_only: bool = False,
            source_names: set[str] | None = None,
        ) -> None:
            observed["demo_only"] = demo_only
            observed["source_names"] = source_names
            observed["pipelines"].append(self.__class__.__name__)
            super().__init__(demo_only=demo_only, source_names=source_names)

    monkeypatch.setattr(
        refresh_live_data_script,
        "ensure_sqlite_schema",
        fake_ensure_sqlite_schema,
    )
    monkeypatch.setattr(
        refresh_live_data_script,
        "PIPELINES",
        {
            "news": ObservedPipeline,
            "traffic": ObservedPipeline,
        },
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "refresh_live_data.py",
            "--pipeline",
            "news",
            "--pipeline",
            "traffic",
            "--source",
            "vnexpress_rss_tin_moi",
        ],
    )

    refresh_live_data_script.main()
    payload = json.loads(capsys.readouterr().out)

    assert observed["schema_checked"] is True
    assert observed["demo_only"] is False
    assert observed["source_names"] == {"vnexpress_rss_tin_moi"}
    assert len(payload["summaries"]) == 2
    assert all(summary["used_demo"] is False for summary in payload["summaries"])
