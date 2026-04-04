from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.core.logging import get_logger
from app.core.settings import get_settings
from app.db.session import session_scope
from app.pipelines.common.fetcher import fetch_source
from app.pipelines.common.raw_storage import RawStorage
from app.pipelines.common.records import PipelineRunSummary, SourceDefinition
from app.pipelines.common.source_loader import load_sources_for_pipeline
from app.repositories.job_repository import JobRepository
from app.repositories.raw_repository import RawDocumentRepository
from app.repositories.source_repository import SourceRepository

RecordT = TypeVar("RecordT")

logger = get_logger(__name__)


class BasePipeline(ABC, Generic[RecordT]):
    pipeline_name: str

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        settings = get_settings()
        self.demo_only = demo_only
        self.source_names = source_names or set()
        self.raw_storage = RawStorage(settings.raw_storage_path)
        self.source_repo = SourceRepository()
        self.job_repo = JobRepository()
        self.raw_repo = RawDocumentRepository()

    @abstractmethod
    def parse(self, source: SourceDefinition, payload: str) -> list[RecordT]:
        raise NotImplementedError

    @abstractmethod
    def store(self, source_id: int | None, records: list[RecordT]) -> int:
        raise NotImplementedError

    def run(self) -> list[PipelineRunSummary]:
        summaries: list[PipelineRunSummary] = []

        sources = load_sources_for_pipeline(self.pipeline_name)
        if self.source_names:
            sources = [source for source in sources if source.name in self.source_names]
        if not sources:
            logger.warning("Khong tim thay source nao cho pipeline %s", self.pipeline_name)
            return summaries

        for definition in sources:
            if not self.demo_only and bool(definition.extra.get("demo_only_source")):
                logger.info(
                    "Bo qua source %s vi chi danh cho che do demo",
                    definition.name,
                )
                summaries.append(
                    PipelineRunSummary(
                        pipeline=self.pipeline_name,
                        source_name=definition.name,
                        total_fetched=0,
                        total_success=0,
                        total_failed=0,
                        status="skipped",
                        used_demo=False,
                        error_message=None,
                        total_skipped=0,
                    )
                )
                continue

            if self.demo_only and not definition.demo_fixture:
                logger.info(
                    "Bo qua source %s vi demo_only dang bat va khong co fixture demo",
                    definition.name,
                )
                summaries.append(
                    PipelineRunSummary(
                        pipeline=self.pipeline_name,
                        source_name=definition.name,
                        total_fetched=0,
                        total_success=0,
                        total_failed=0,
                        status="skipped",
                        used_demo=False,
                        error_message=None,
                        total_skipped=0,
                    )
                )
                continue

            total_fetched = 0
            total_success = 0
            total_failed = 0
            total_skipped = 0
            used_demo = False
            error_message = None
            status = "failed"
            source_id: int | None = None
            job_id: int | None = None

            try:
                with session_scope() as db:
                    source_row = self.source_repo.sync_from_definition(db, definition)
                    source_id = source_row.id
                    job = self.job_repo.start_job(db, self.pipeline_name, source_row.id)
                    job_id = job.id

                fetch_result = fetch_source(definition, demo_only=self.demo_only)
                used_demo = fetch_result.used_demo
                extension = "json"
                if "html" in (fetch_result.content_type or ""):
                    extension = "html"
                elif "rss" in (fetch_result.content_type or "") or "xml" in (
                    fetch_result.content_type or ""
                ):
                    extension = "xml"

                raw_path, raw_hash = self.raw_storage.save_text(
                    pipeline_name=self.pipeline_name,
                    source_name=definition.name,
                    content=fetch_result.text,
                    extension=extension,
                )
                with session_scope() as db:
                    self.raw_repo.create(
                        db,
                        source_id=source_id,
                        pipeline_name=self.pipeline_name,
                        fetch_url=fetch_result.source_url,
                        content_type=fetch_result.content_type,
                        raw_path_or_text=raw_path,
                        raw_hash=raw_hash,
                        fetch_metadata={"used_demo": used_demo},
                    )

                definition.extra["_used_demo"] = used_demo
                records = self.parse(definition, fetch_result.text)
                total_fetched = len(records)
                total_success = self.store(source_id, records)
                total_skipped = max(total_fetched - total_success, 0)
                total_failed = 0
                status = "success"
            except Exception as exc:
                total_failed = max(total_fetched, 1)
                error_message = str(exc)
                logger.exception(
                    "Pipeline %s loi voi source %s", self.pipeline_name, definition.name
                )

            if job_id is not None:
                with session_scope() as db:
                    job = self.job_repo.get_by_id(db, job_id)
                    if job is not None:
                        self.job_repo.finish_job(
                            db,
                            job,
                            status=status,
                            total_fetched=total_fetched,
                            total_success=total_success,
                            total_failed=total_failed,
                            error_message=error_message,
                            metadata_json={
                                "used_demo": used_demo,
                                "total_skipped": total_skipped,
                            },
                        )

            summaries.append(
                PipelineRunSummary(
                    pipeline=self.pipeline_name,
                    source_name=definition.name,
                    total_fetched=total_fetched,
                    total_success=total_success,
                    total_failed=total_failed,
                    status=status,
                    used_demo=used_demo,
                    error_message=error_message,
                    total_skipped=total_skipped,
                )
            )
        return summaries
