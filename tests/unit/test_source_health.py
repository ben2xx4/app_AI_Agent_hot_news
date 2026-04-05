from __future__ import annotations

import json
from pathlib import Path

from app.pipelines.common.records import SourceDefinition
from app.ui.source_health import load_scheduler_health_snapshot


def test_scheduler_health_snapshot_reports_uninitialized_file(tmp_path: Path) -> None:
    status_path = tmp_path / "scheduler_status.json"
    sources = [
        SourceDefinition(
            name="vnexpress_rss_tin_moi",
            pipeline="news",
            source_type="rss",
            fetch_interval_minutes=10,
        )
    ]

    snapshot = load_scheduler_health_snapshot(
        status_path=status_path,
        sources=sources,
    )

    assert snapshot["initialized"] is False
    assert snapshot["configured_sources"] == 1
    assert snapshot["attention_jobs"] == []


def test_scheduler_health_snapshot_filters_demo_only_sources_in_live_mode(tmp_path: Path) -> None:
    status_path = tmp_path / "scheduler_status.json"
    status_path.write_text(
        json.dumps(
            {
                "price:sjc_gold_prices": {
                    "run_count": 1,
                    "last_status": "success",
                    "last_finished_at": "2026-04-04T18:00:00",
                    "last_started_at": "2026-04-04T18:00:00",
                    "last_total_fetched": 3,
                    "last_total_success": 3,
                    "last_total_failed": 0,
                    "failure_streak": 0,
                    "last_duration_seconds": 0.1,
                },
                "news:vnexpress_rss_tin_moi": {
                    "run_count": 1,
                    "last_status": "failed",
                    "last_finished_at": "2026-04-04T18:00:00",
                    "last_started_at": "2026-04-04T18:00:00",
                    "last_total_fetched": 10,
                    "last_total_success": 0,
                    "last_total_failed": 10,
                    "failure_streak": 2,
                    "last_duration_seconds": 4.2,
                    "last_error_message": "Loi parser",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    sources = [
        SourceDefinition(
            name="sjc_gold_prices",
            pipeline="price",
            source_type="json",
            fetch_interval_minutes=15,
            extra={"demo_only_source": True},
        ),
        SourceDefinition(
            name="vnexpress_rss_tin_moi",
            pipeline="news",
            source_type="rss",
            fetch_interval_minutes=10,
        ),
    ]

    snapshot = load_scheduler_health_snapshot(
        status_path=status_path,
        sources=sources,
        demo_only=False,
    )

    assert snapshot["initialized"] is True
    assert snapshot["configured_sources"] == 1
    assert snapshot["summary"]["failing_jobs"] == 1
    assert snapshot["attention_jobs"][0]["source_name"] == "vnexpress_rss_tin_moi"
    assert all(job["source_name"] != "sjc_gold_prices" for job in snapshot["jobs"])
