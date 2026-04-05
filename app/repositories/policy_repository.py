from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.text import contains_folded, expand_policy_query, fold_text
from app.models import PolicyDocument
from app.pipelines.common.processing import normalize_datetime_for_compare

PREFER_RECENT_POLICY_DAYS = 90


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
        self,
        db: Session,
        query: str | None = None,
        field: str | None = None,
        limit: int = 10,
        reference_now: datetime | None = None,
    ) -> list[PolicyDocument]:
        stmt = select(PolicyDocument).order_by(
            desc(PolicyDocument.issued_at), desc(PolicyDocument.id)
        )
        rows = list(db.scalars(stmt))
        queries = expand_policy_query(query) or [query]
        current_time = normalize_datetime_for_compare(reference_now or datetime.now(UTC))

        filtered_rows: list[tuple[int, PolicyDocument]] = []
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
                filtered_rows.append(
                    (
                        self._build_relevance_score(
                            row,
                            queries=queries,
                            field=field,
                            reference_now=current_time,
                        ),
                        row,
                    )
                )

        filtered_rows.sort(
            key=lambda item: (
                item[0],
                item[1].issued_at or datetime.min,
                item[1].id or 0,
            ),
            reverse=True,
        )

        deduped: list[PolicyDocument] = []
        seen: set[str] = set()
        for _, row in filtered_rows:
            key = row.canonical_url or f"{row.doc_number}:{row.title}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        return deduped[:limit]

    def _build_relevance_score(
        self,
        row: PolicyDocument,
        *,
        queries: list[str | None],
        field: str | None,
        reference_now: datetime,
    ) -> int:
        score = 0
        for candidate in queries:
            folded_query = fold_text(candidate)
            if not folded_query:
                continue
            if contains_folded(row.doc_number, folded_query):
                score += 14
            if contains_folded(row.title, folded_query):
                score += 10
            if contains_folded(row.field, folded_query):
                score += 8
            if contains_folded(row.summary, folded_query):
                score += 6
            if contains_folded(row.issuing_agency, folded_query):
                score += 4
            if contains_folded(row.content_clean, folded_query):
                score += 3

        if field:
            score += 4 if contains_folded(row.field, field) else 0

        if row.issued_at is not None:
            issued_at = normalize_datetime_for_compare(row.issued_at)
            age_days = max((reference_now - issued_at).days, 0)
            if age_days <= PREFER_RECENT_POLICY_DAYS:
                score += 5
            elif age_days <= PREFER_RECENT_POLICY_DAYS * 2:
                score += 2
        return score
