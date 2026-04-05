from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.settings import get_settings
from app.pipelines.common.records import SourceDefinition
from app.services.scheduler_service import SchedulerService

HEALTH_PRIORITY = {
    "failing": 0,
    "due": 1,
    "pending": 2,
    "running": 3,
    "healthy": 4,
}

ATTENTION_STATES = {"failing", "due", "pending", "running"}


def load_scheduler_health_snapshot(
    *,
    demo_only: bool = False,
    status_path: Path | None = None,
    pipeline_names: set[str] | None = None,
    source_names: set[str] | None = None,
    sources: list[SourceDefinition] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    effective_status_path = status_path or (
        settings.processed_storage_path / "scheduler_status.json"
    )
    service = SchedulerService(
        demo_only=demo_only,
        status_path=effective_status_path,
        pipeline_names=pipeline_names,
        source_names=source_names,
        sources=sources,
    )
    configured_sources = len(service.sources)
    if not effective_status_path.exists():
        return {
            "initialized": False,
            "status_path": str(effective_status_path),
            "configured_sources": configured_sources,
            "summary": None,
            "attention_jobs": [],
            "jobs": [],
        }

    jobs = service.dump_status()
    summary = service.dump_health_summary()
    attention_jobs = sorted(
        [job for job in jobs if job["health_state"] in ATTENTION_STATES],
        key=lambda job: (
            HEALTH_PRIORITY.get(job["health_state"], 99),
            job["pipeline"],
            job["source_name"],
        ),
    )
    return {
        "initialized": True,
        "status_path": str(effective_status_path),
        "configured_sources": configured_sources,
        "summary": summary,
        "attention_jobs": attention_jobs,
        "jobs": jobs,
    }
