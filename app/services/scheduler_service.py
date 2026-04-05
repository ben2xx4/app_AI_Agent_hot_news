from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.pipelines.common.records import SourceDefinition
from app.pipelines.common.source_loader import load_source_definitions
from app.pipelines.news.pipeline import NewsPipeline
from app.pipelines.policy.pipeline import PolicyPipeline
from app.pipelines.price.pipeline import PricePipeline
from app.pipelines.traffic.pipeline import TrafficPipeline
from app.pipelines.weather.pipeline import WeatherPipeline

logger = get_logger(__name__)

PIPELINE_REGISTRY = {
    "news": NewsPipeline,
    "price": PricePipeline,
    "weather": WeatherPipeline,
    "policy": PolicyPipeline,
    "traffic": TrafficPipeline,
}


@dataclass(slots=True)
class SchedulerJobView:
    pipeline: str
    source_name: str
    interval_minutes: int
    due: bool
    last_started_at: str | None
    last_finished_at: str | None
    last_status: str | None
    last_total_fetched: int
    last_total_success: int
    last_total_failed: int
    last_error_message: str | None
    next_run_at: str | None
    run_count: int
    health_state: str
    failure_streak: int
    last_duration_seconds: float | None


@dataclass(slots=True)
class SchedulerHealthSummary:
    total_jobs: int
    healthy_jobs: int
    due_jobs: int
    pending_jobs: int
    failing_jobs: int
    attention_sources: list[str]


class SchedulerStatusStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


class SchedulerService:
    def __init__(
        self,
        *,
        demo_only: bool = False,
        status_path: Path | None = None,
        pipeline_names: set[str] | None = None,
        source_names: set[str] | None = None,
        sources: list[SourceDefinition] | None = None,
        pipeline_registry: dict[str, type] | None = None,
        status_store: SchedulerStatusStore | None = None,
    ) -> None:
        settings = get_settings()
        self.timezone = ZoneInfo(settings.timezone)
        self.demo_only = demo_only
        self.pipeline_names = pipeline_names or set()
        self.source_names = source_names or set()
        self.sources = self._filter_sources(sources or load_source_definitions())
        self.pipeline_registry = pipeline_registry or PIPELINE_REGISTRY
        default_status_path = settings.processed_storage_path / "scheduler_status.json"
        self.status_store = status_store or SchedulerStatusStore(status_path or default_status_path)

    def _filter_sources(self, sources: list[SourceDefinition]) -> list[SourceDefinition]:
        filtered = [source for source in sources if source.active]
        if not self.demo_only:
            filtered = [
                source
                for source in filtered
                if not bool(source.extra.get("demo_only_source"))
            ]
        if self.pipeline_names:
            filtered = [source for source in filtered if source.pipeline in self.pipeline_names]
        if self.source_names:
            filtered = [source for source in filtered if source.name in self.source_names]
        return filtered

    def _job_key(self, source: SourceDefinition) -> str:
        return f"{source.pipeline}:{source.name}"

    def _parse_time(self, value: str | None) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value)
        return self._normalize_time(parsed)

    def _serialize_time(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        return self._normalize_time(value).isoformat()

    def _normalize_time(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value.astimezone(self.timezone)

    def _current_time(self, now: datetime | None = None) -> datetime:
        if now is None:
            return datetime.now(self.timezone)
        return self._normalize_time(now)

    def _compute_next_run_at(
        self,
        source: SourceDefinition,
        state: dict[str, Any],
        *,
        now: datetime,
    ) -> datetime | None:
        if not state.get("last_finished_at"):
            return now
        last_finished_at = self._parse_time(state.get("last_finished_at"))
        if last_finished_at is None:
            return now
        return last_finished_at + timedelta(minutes=source.fetch_interval_minutes)

    def _derive_health_state(
        self,
        *,
        state: dict[str, Any],
        next_run_at: datetime | None,
        now: datetime,
    ) -> str:
        run_count = int(state.get("run_count", 0))
        last_status = state.get("last_status")
        failure_streak = int(state.get("failure_streak", 0))
        if last_status == "running":
            return "running"
        if run_count == 0:
            return "pending"
        if failure_streak > 0 or last_status == "failed":
            return "failing"
        if next_run_at is None or next_run_at <= now:
            return "due"
        return "healthy"

    def list_jobs(self, *, now: datetime | None = None) -> list[SchedulerJobView]:
        current_time = self._current_time(now)
        states = self.status_store.load()
        jobs: list[SchedulerJobView] = []

        for source in self.sources:
            state = states.get(self._job_key(source), {})
            next_run_at = self._compute_next_run_at(source, state, now=current_time)
            due = next_run_at is None or next_run_at <= current_time
            health_state = self._derive_health_state(
                state=state,
                next_run_at=next_run_at,
                now=current_time,
            )
            jobs.append(
                SchedulerJobView(
                    pipeline=source.pipeline,
                    source_name=source.name,
                    interval_minutes=source.fetch_interval_minutes,
                    due=due,
                    last_started_at=state.get("last_started_at"),
                    last_finished_at=state.get("last_finished_at"),
                    last_status=state.get("last_status"),
                    last_total_fetched=int(state.get("last_total_fetched", 0)),
                    last_total_success=int(state.get("last_total_success", 0)),
                    last_total_failed=int(state.get("last_total_failed", 0)),
                    last_error_message=state.get("last_error_message"),
                    next_run_at=self._serialize_time(next_run_at),
                    run_count=int(state.get("run_count", 0)),
                    health_state=health_state,
                    failure_streak=int(state.get("failure_streak", 0)),
                    last_duration_seconds=state.get("last_duration_seconds"),
                )
            )
        return jobs

    def run_due_jobs(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        current_time = self._current_time(now)
        results: list[dict[str, Any]] = []
        for job in self.list_jobs(now=current_time):
            if not job.due:
                continue
            source = next(
                item
                for item in self.sources
                if item.pipeline == job.pipeline and item.name == job.source_name
            )
            results.append(self.run_source(source, now=current_time))
        return results

    def run_source(
        self,
        source: SourceDefinition,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current_time = self._current_time(now)
        states = self.status_store.load()
        key = self._job_key(source)
        state = states.get(key, {})
        state["last_started_at"] = self._serialize_time(current_time)
        state["last_status"] = "running"
        states[key] = state
        self.status_store.save(states)

        pipeline_cls = self.pipeline_registry[source.pipeline]
        logger.info("Scheduler chay source %s (%s)", source.name, source.pipeline)
        started_perf = time.perf_counter()
        pipeline = pipeline_cls(demo_only=self.demo_only, source_names={source.name})
        summaries = pipeline.run()
        summary = summaries[0] if summaries else None

        elapsed_seconds = max(time.perf_counter() - started_perf, 0.0)
        finished_at = current_time + timedelta(seconds=elapsed_seconds)
        state["last_finished_at"] = self._serialize_time(finished_at)
        state["last_status"] = summary.status if summary else "unknown"
        state["last_total_fetched"] = summary.total_fetched if summary else 0
        state["last_total_success"] = summary.total_success if summary else 0
        state["last_total_failed"] = summary.total_failed if summary else 0
        state["last_error_message"] = summary.error_message if summary else None
        state["run_count"] = int(state.get("run_count", 0)) + 1
        state["last_duration_seconds"] = round(elapsed_seconds, 3)
        if state["last_status"] == "success":
            state["failure_streak"] = 0
            state["last_success_at"] = self._serialize_time(finished_at)
        else:
            state["failure_streak"] = int(state.get("failure_streak", 0)) + 1
        states[key] = state
        self.status_store.save(states)

        next_run_at = self._compute_next_run_at(source, state, now=finished_at)
        health_state = self._derive_health_state(
            state=state,
            next_run_at=next_run_at,
            now=finished_at,
        )
        payload = {
            "pipeline": source.pipeline,
            "source_name": source.name,
            "status": state["last_status"],
            "total_fetched": state["last_total_fetched"],
            "total_success": state["last_total_success"],
            "total_failed": state["last_total_failed"],
            "error_message": state["last_error_message"],
            "run_count": state["run_count"],
            "failure_streak": state["failure_streak"],
            "last_duration_seconds": state["last_duration_seconds"],
            "health_state": health_state,
            "next_run_at": self._serialize_time(next_run_at),
        }
        logger.info("Scheduler xong source %s: %s", source.name, payload["status"])
        return payload

    def dump_status(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        return [asdict(job) for job in self.list_jobs(now=now)]

    def dump_health_summary(self, *, now: datetime | None = None) -> dict[str, Any]:
        jobs = self.list_jobs(now=now)
        attention_states = {"failing", "due", "pending"}
        summary = SchedulerHealthSummary(
            total_jobs=len(jobs),
            healthy_jobs=sum(1 for job in jobs if job.health_state == "healthy"),
            due_jobs=sum(1 for job in jobs if job.health_state == "due"),
            pending_jobs=sum(1 for job in jobs if job.health_state == "pending"),
            failing_jobs=sum(1 for job in jobs if job.health_state == "failing"),
            attention_sources=[
                f"{job.pipeline}:{job.source_name}"
                for job in jobs
                if job.health_state in attention_states
            ],
        )
        return asdict(summary)
