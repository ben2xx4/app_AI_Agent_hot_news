from __future__ import annotations

from app.core.settings import get_settings
from app.db.session import session_scope
from app.pipelines.common.base import BasePipeline
from app.pipelines.common.processing import split_into_chunks
from app.pipelines.common.records import PolicyRecord, SourceDefinition
from app.pipelines.policy.parser import parse_policy_payload
from app.repositories.embedding_repository import EmbeddingRepository
from app.repositories.policy_repository import PolicyRepository
from app.services.retrieval_index_service import build_chunk_vectors


class PolicyPipeline(BasePipeline[PolicyRecord]):
    pipeline_name = "policy"

    def __init__(self, *, demo_only: bool = False, source_names: set[str] | None = None) -> None:
        super().__init__(demo_only=demo_only, source_names=source_names)
        self.policy_repo = PolicyRepository()
        self.embedding_repo = EmbeddingRepository()

    def parse(self, source: SourceDefinition, payload: str) -> list[PolicyRecord]:
        return parse_policy_payload(source, payload)

    def store(self, source_id: int | None, records: list[PolicyRecord]) -> int:
        inserted = 0
        with session_scope() as db:
            for record in records:
                if record.canonical_url and self.policy_repo.get_by_canonical_url(
                    db, record.canonical_url
                ):
                    continue
                created = self.policy_repo.create_document(
                    db,
                    source_id=source_id,
                    issuing_agency=record.issuing_agency,
                    doc_number=record.doc_number,
                    title=record.title,
                    summary=record.summary,
                    content_clean=record.content_clean,
                    field=record.field,
                    issued_at=record.issued_at,
                    effective_at=record.effective_at,
                    canonical_url=record.canonical_url,
                )
                chunks = split_into_chunks(record.content_clean or record.summary, max_chars=450)
                if chunks:
                    self.embedding_repo.replace_chunks(
                        db,
                        doc_type="policy",
                        doc_id=created.id,
                        chunks=chunks,
                        embedding_model=get_settings().experimental_retrieval_model,
                        embedding_vectors=build_chunk_vectors(chunks),
                    )
                inserted += 1
        return inserted
