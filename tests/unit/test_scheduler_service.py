from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

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


class FakeFailingPipeline:
    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        self.demo_only = demo_only
        self.source_names = source_names or set()

    def run(self) -> list[PipelineRunSummary]:
        return [
            PipelineRunSummary(
                pipeline="news",
                source_name=next(iter(self.source_names)),
                total_fetched=1,
                total_success=0,
                total_failed=1,
                status="failed",
                used_demo=self.demo_only,
                error_message="Nguon tam thoi loi",
            )
        ]


class FakeSlowPipeline:
    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        self.demo_only = demo_only
        self.source_names = source_names or set()

    def run(self) -> list[PipelineRunSummary]:
        time.sleep(0.02)
        return [
            PipelineRunSummary(
                pipeline="news",
                source_name=next(iter(self.source_names)),
                total_fetched=1,
                total_success=1,
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
    assert jobs[0]["health_state"] == "healthy"
    assert jobs[0]["failure_streak"] == 0

    second_runs = service.run_due_jobs(now=now + timedelta(minutes=11))
    assert len(second_runs) == 1
    assert second_runs[0]["run_count"] == 2
    assert second_runs[0]["health_state"] == "healthy"


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


def test_scheduler_service_tracks_failure_streak_and_health_summary(tmp_path: Path) -> None:
    now = datetime(2026, 4, 4, 8, 0, 0)
    status_path = tmp_path / "scheduler_status.json"
    sources = [
        SourceDefinition(
            name="vnexpress_rss_tin_moi",
            pipeline="news",
            source_type="rss",
            fetch_interval_minutes=10,
        ),
        SourceDefinition(
            name="dantri_rss_tin_moi",
            pipeline="news",
            source_type="rss",
            fetch_interval_minutes=10,
        ),
    ]
    service = SchedulerService(
        demo_only=False,
        status_path=status_path,
        sources=sources,
        pipeline_registry={"news": FakeFailingPipeline},
    )

    first_run = service.run_source(sources[0], now=now)
    second_run = service.run_source(sources[0], now=now + timedelta(minutes=11))

    assert first_run["health_state"] == "failing"
    assert second_run["failure_streak"] == 2
    assert second_run["health_state"] == "failing"

    jobs = service.dump_status(now=now + timedelta(minutes=12))
    assert jobs[0]["failure_streak"] == 2
    assert jobs[0]["health_state"] == "failing"
    assert jobs[1]["health_state"] == "pending"

    summary = service.dump_health_summary(now=now + timedelta(minutes=12))
    assert summary["total_jobs"] == 2
    assert summary["failing_jobs"] == 1
    assert summary["pending_jobs"] == 1
    assert "news:vnexpress_rss_tin_moi" in summary["attention_sources"]
    assert "news:dantri_rss_tin_moi" in summary["attention_sources"]


def test_scheduler_service_records_non_zero_duration(tmp_path: Path) -> None:
    now = datetime(2026, 4, 4, 8, 0, 0)
    status_path = tmp_path / "scheduler_status.json"
    source = SourceDefinition(
        name="vnexpress_rss_tin_moi",
        pipeline="news",
        source_type="rss",
        fetch_interval_minutes=10,
    )
    service = SchedulerService(
        demo_only=False,
        status_path=status_path,
        sources=[source],
        pipeline_registry={"news": FakeSlowPipeline},
    )

    payload = service.run_source(source, now=now)

    assert payload["last_duration_seconds"] > 0
    jobs = service.dump_status(now=now + timedelta(minutes=1))
    assert jobs[0]["last_duration_seconds"] > 0


def test_scheduler_service_interprets_legacy_naive_status_as_local_timezone(
    tmp_path: Path,
) -> None:
    status_path = tmp_path / "scheduler_status.json"
    status_path.write_text(
        """
        {
          "news:vnexpress_rss_tin_moi": {
            "last_started_at": "2026-04-04T22:19:16.753962",
            "last_finished_at": "2026-04-04T22:19:16.753962",
            "last_status": "success",
            "last_total_fetched": 40,
            "last_total_success": 0,
            "last_total_failed": 0,
            "run_count": 1,
            "failure_streak": 0
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    source = SourceDefinition(
        name="vnexpress_rss_tin_moi",
        pipeline="news",
        source_type="rss",
        fetch_interval_minutes=10,
    )
    service = SchedulerService(
        demo_only=False,
        status_path=status_path,
        sources=[source],
        pipeline_registry={"news": FakeNewsPipeline},
    )

    jobs = service.dump_status(
        now=datetime(2026, 4, 5, 1, 0, 0, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    )

    assert jobs[0]["due"] is True
    assert jobs[0]["health_state"] == "due"
