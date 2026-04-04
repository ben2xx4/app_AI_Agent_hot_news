from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.text import contains_folded, expand_policy_query
from app.models import PolicyDocument


class PolicyRepository:
    def create_document(self, db: Session, **payload) -> PolicyDocument:
        document = PolicyDocument(**payload)
        db.add(document)
        db.flush()
        return document

    def get_by_canonical_url(self, db: Session, canonical_url: str) -> PolicyDocument | None:
        stmt = select(PolicyDocument).where(PolicyDocument.canonical_url == canonical_url)
        return db.scalar(stmt)

    def get_by_ids(self, db: Session, ids: list[int]) -> list[PolicyDocument]:
        if not ids:
            return []
        stmt = select(PolicyDocument).where(PolicyDocument.id.in_(ids))
        rows = list(db.scalars(stmt))
        rows_by_id = {row.id: row for row in rows}
        return [rows_by_id[row_id] for row_id in ids if row_id in rows_by_id]

    def search(
        self, db: Session, query: str | None = None, field: str | None = None, limit: int = 10
    ) -> list[PolicyDocument]:
        stmt = select(PolicyDocument).order_by(
            desc(PolicyDocument.issued_at), desc(PolicyDocument.id)
        )
        rows = list(db.scalars(stmt))
        queries = expand_policy_query(query) or [query]

        filtered_rows = []
        for row in rows:
            matches_query = any(
                contains_folded(value, candidate)
                for value in [
                    row.title,
                    row.summary,
                    row.content_clean,
                    row.field,
                    row.issuing_agency,
                ]
                for candidate in queries
            )
            matches_field = contains_folded(row.field, field)
            if matches_query and matches_field:
                filtered_rows.append(row)

        deduped: list[PolicyDocument] = []
        seen: set[str] = set()
        for row in filtered_rows:
            key = row.canonical_url or f"{row.doc_number}:{row.title}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped[:limit]
