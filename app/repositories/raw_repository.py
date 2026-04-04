from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import RawDocument


class RawDocumentRepository:
    def create(
        self,
        db: Session,
        *,
        source_id: int | None,
        pipeline_name: str,
        fetch_url: str | None,
        content_type: str | None,
        raw_path_or_text: str,
        raw_hash: str,
        fetch_metadata: dict | None,
    ) -> RawDocument:
        raw_document = RawDocument(
            source_id=source_id,
            pipeline_name=pipeline_name,
            fetch_url=fetch_url,
            content_type=content_type,
            raw_path_or_text=raw_path_or_text,
            raw_hash=raw_hash,
            fetch_metadata=fetch_metadata,
        )
        db.add(raw_document)
        db.flush()
        return raw_document
