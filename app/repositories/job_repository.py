from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import CrawlJob


class JobRepository:
    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    def get_by_id(self, db: Session, job_id: int) -> CrawlJob | None:
        return db.get(CrawlJob, job_id)

    def start_job(self, db: Session, pipeline_name: str, source_id: int | None) -> CrawlJob:
        job = CrawlJob(
            pipeline_name=pipeline_name,
            source_id=source_id,
            status="running",
            started_at=self._utcnow_naive(),
        )
        db.add(job)
        db.flush()
        return job

    def finish_job(
        self,
        db: Session,
        job: CrawlJob,
        *,
        status: str,
        total_fetched: int,
        total_success: int,
        total_failed: int,
        error_message: str | None = None,
        metadata_json: dict | None = None,
    ) -> CrawlJob:
        job.status = status
        job.finished_at = self._utcnow_naive()
        job.total_fetched = total_fetched
        job.total_success = total_success
        job.total_failed = total_failed
        job.error_message = error_message
        job.metadata_json = metadata_json
        db.add(job)
        db.flush()
        return job
