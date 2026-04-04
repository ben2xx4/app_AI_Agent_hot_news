from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from app.pipelines.common.records import PipelineRunSummary, SourceDefinition
from app.services.scheduler_service import SchedulerService


class FakeNewsPipeline:
    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        self.demo_only = demo_only
        self.source_names = source_names or set()

    def run(self) -> list[PipelineRunSummary]:
        return [
            PipelineRunSummary(
                pipeline="news",
                source_name=next(iter(self.source_names)),
                total_fetched=3,
                total_success=3,
                total_failed=0,
                status="success",
                used_demo=self.demo_only,
                error_message=None,
            )
        ]


def test_scheduler_service_runs_due_sources_and_updates_status(tmp_path: Path) -> None:
    now = datetime(2026, 4, 4, 8, 0, 0)
    status_path = tmp_path / "scheduler_status.json"
    source = SourceDefinition(
        name="tuoitre_rss_thoi_su",
        pipeline="news",
        source_type="rss",
        fetch_interval_minutes=10,
    )
    service = SchedulerService(
        demo_only=True,
        status_path=status_path,
        sources=[source],
        pipeline_registry={"news": FakeNewsPipeline},
    )

    first_runs = service.run_due_jobs(now=now)
    assert len(first_runs) == 1
    assert first_runs[0]["status"] == "success"

    jobs = service.dump_status(now=now + timedelta(minutes=1))
    assert jobs[0]["run_count"] == 1
    assert jobs[0]["due"] is False

    second_runs = service.run_due_jobs(now=now + timedelta(minutes=11))
    assert len(second_runs) == 1
    assert second_runs[0]["run_count"] == 2


def test_scheduler_service_filters_pipeline_and_source(tmp_path: Path) -> None:
    status_path = tmp_path / "scheduler_status.json"
    sources = [
        SourceDefinition(
            name="tuoitre_rss_thoi_su",
            pipeline="news",
            source_type="rss",
            fetch_interval_minutes=10,
        ),
        SourceDefinition(
            name="vietcombank_fx_rates_live",
            pipeline="price",
            source_type="xml",
            fetch_interval_minutes=30,
        ),
    ]
    service = SchedulerService(
        demo_only=False,
        status_path=status_path,
        sources=sources,
        pipeline_names={"price"},
        source_names={"vietcombank_fx_rates_live"},
        pipeline_registry={"price": FakeNewsPipeline},
    )

    jobs = service.dump_status(now=datetime(2026, 4, 4, 8, 0, 0))
    assert len(jobs) == 1
    assert jobs[0]["pipeline"] == "price"
    assert jobs[0]["source_name"] == "vietcombank_fx_rates_live"
